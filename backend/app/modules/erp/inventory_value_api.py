"""
棚卸金額計算・照会 API
inventory_logs をもとに金額を計算する。
部品明細は `parts.part_name` / `parts.total_unit_price`（part_cd = ログの product_cd）を使用する。
部品以外の単価累計は `product_cost_cumulative_snapshots.cumulative_unit_price`（is_latest=1）を
優先し、無い場合のみ従来のルート内積算にフォールバックする。
"""
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, or_, tuple_, cast, Numeric, asc, desc, exists
from sqlalchemy.exc import ProgrammingError
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal

from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.core.database import get_db
from app.modules.master.models import (
    ProductProcessUnitPrice,
    ProductRouteStep,
    Product,
    ProductBomHeader,
    ProductBomLine,
    Material,
    PartMaster,
    Process,
    InventoryValueCalcRun,
    InventoryValueCalcDetail,
    ProductCostCumulativeSnapshot,
    Destination,
)
from app.modules.database.models import ProductionSummary
from app.modules.material.models import MaterialStock
from app.modules.part.models import PartStock
from app.modules.erp.models import OrderDaily

router = APIRouter(prefix="/inventory-value", tags=["棚卸金額"])

# process_cd → production_summarys.*_inventory（app.modules.database.api と同定義）
_PROCESS_CD_TO_INVENTORY_COL: Dict[str, str] = {
    "KT01": "cutting_inventory",
    "KT02": "chamfering_inventory",
    "KT04": "molding_inventory",
    "KT05": "plating_inventory",
    "KT06": "outsourced_plating_inventory",
    "KT07": "welding_inventory",
    "KT08": "outsourced_welding_inventory",
    "KT09": "inspection_inventory",
    "KT13": "warehouse_inventory",
    "KT10": "outsourced_warehouse_inventory",
    "KT15": "outsourced_warehouse_inventory",
    "KT11": "pre_welding_inspection_inventory",
    "KT16": "pre_inspection_inventory",
    "KT17": "pre_outsourcing_inventory",
}
_ALLOWED_INVENTORY_COLS = frozenset(_PROCESS_CD_TO_INVENTORY_COL.values())


def _parse_as_of_date(value: str) -> date:
    s = (value or "").strip()[:10]
    try:
        y, m, d = [int(x) for x in s.split("-")]
        return date(y, m, d)
    except Exception:
        raise HTTPException(status_code=422, detail="as_of は YYYY-MM-DD 形式で指定してください")


def _inventory_col_for_process(process_cd: Optional[str]) -> str:
    if not process_cd or str(process_cd).strip().lower() in ("all", ""):
        return "warehouse_inventory"
    col = _PROCESS_CD_TO_INVENTORY_COL.get(str(process_cd).strip())
    if col and col in _ALLOWED_INVENTORY_COLS:
        return col
    return "warehouse_inventory"


def _fnum(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    try:
        return float(v)
    except Exception:
        return 0.0


# ---------- Schemas ----------

class CalcRequest(BaseModel):
    start_date: str
    end_date: str
    process_cd: Optional[str] = None


# ---------- Helpers（単価累計＝加工費 + BOM 材料・部品を工程別に積み上げ） ----------
# ProductProcessUnitPriceEditor.vue の「単価累計（工程完了時点）」と同じ考え方。


def _uom_is_mass_kg(uom: str) -> bool:
    u = (uom or "").strip().lower().replace(" ", "").replace("\u3000", "")
    return u in ("kg", "キロ", "ｋｇ", "kgs", "kilogram")


def _uom_is_mass_g(uom: str) -> bool:
    u = (uom or "").strip().lower().replace(" ", "").replace("\u3000", "")
    return u in ("g", "gr", "グラム", "ｇ")


def _material_line_amount(line: ProductBomLine, mat: Optional[Material], take_count: int) -> Decimal:
    """BOM 材料行の金額（親製品 1 個あたり）。フロント materialCostFromLine と同式。"""
    tc = take_count if take_count and take_count > 0 else 1
    qty_per = Decimal(str(line.qty_per or 0))
    scrap = Decimal(str(line.scrap_rate or 0))
    qty_eff = qty_per * (Decimal(1) + scrap / Decimal(100))
    uom = line.uom or ""
    unit_price = Decimal(str(mat.unit_price or 0)) if mat else Decimal("0")
    long_w = Decimal(str(mat.long_weight or 0)) if mat else Decimal("0")
    single_p = Decimal(str(mat.single_price or 0)) if mat else Decimal("0")
    tc_dec = Decimal(tc)

    if _uom_is_mass_kg(uom):
        w = qty_eff
        return (w / tc_dec) * unit_price
    if _uom_is_mass_g(uom):
        kg = qty_eff / Decimal(1000)
        return (kg / tc_dec) * unit_price
    if long_w > 0 and unit_price > 0:
        w = qty_eff * long_w
        return (w / tc_dec) * unit_price
    if single_p > 0:
        return (qty_eff * single_p) / tc_dec
    w_fb = qty_eff * long_w if long_w > 0 else None
    if w_fb is not None and unit_price > 0:
        return (w_fb / tc_dec) * unit_price
    return (qty_eff * unit_price) / tc_dec


def _part_line_amount(line: ProductBomLine, part: Optional[PartMaster], prod: Optional[Product]) -> Decimal:
    """BOM 部品行の金額（親製品 1 個あたり）。フロントと同様 qtyEff × 部品単価。"""
    qty_per = Decimal(str(line.qty_per or 0))
    scrap = Decimal(str(line.scrap_rate or 0))
    qty_eff = qty_per * (Decimal(1) + scrap / Decimal(100))
    from_part = Decimal("0")
    if part is not None:
        tp = getattr(part, "total_unit_price", None)
        if tp is not None:
            from_part = Decimal(str(tp))
        else:
            from_part = Decimal(str(part.unit_price or 0)) + Decimal(str(part.material_unit_price or 0))
    from_prod = Decimal(str(prod.unit_price or 0)) if prod else Decimal("0")
    part_up = from_part if from_part > 0 else from_prod
    return qty_eff * part_up


async def _load_route_steps_ordered(db: AsyncSession, product_cd: str, route_cd: str) -> List[ProductRouteStep]:
    q = (
        select(ProductRouteStep)
        .where(ProductRouteStep.product_cd == product_cd, ProductRouteStep.route_cd == route_cd)
        .order_by(ProductRouteStep.step_no)
    )
    return list((await db.execute(q)).scalars().all())


async def _resolve_bom_header_id_for_valuation(db: AsyncSession, parent_product_cd: str) -> Optional[int]:
    """
    ProductProcessUnitPriceEditor.loadBomForProduct と同じ優先度:
    1) status=active のうち id 最大
    2) 無ければ同一親の最新ヘッダ（任意 status、id desc）
    前者のみだと active が無い環境で BOM が読めず材料・部品が常に 0 になる。
    """
    q_active = (
        select(ProductBomHeader.id)
        .where(
            ProductBomHeader.parent_product_cd == parent_product_cd,
            ProductBomHeader.status == "active",
        )
        .order_by(ProductBomHeader.id.desc())
        .limit(1)
    )
    hid = (await db.execute(q_active)).scalar_one_or_none()
    if hid is not None:
        return hid
    q_any = (
        select(ProductBomHeader.id)
        .where(ProductBomHeader.parent_product_cd == parent_product_cd)
        .order_by(ProductBomHeader.id.desc())
        .limit(1)
    )
    return (await db.execute(q_any)).scalar_one_or_none()


async def _flatten_bom_component_lines(db: AsyncSession, header_id: int) -> List[ProductBomLine]:
    q = (
        select(ProductBomLine)
        .where(ProductBomLine.header_id == header_id)
        .order_by(ProductBomLine.line_no)
    )
    all_lines = list((await db.execute(q)).scalars().all())
    children: dict[int, List[ProductBomLine]] = defaultdict(list)
    roots: List[ProductBomLine] = []
    for ln in all_lines:
        pid = ln.parent_line_id
        if pid:
            children[pid].append(ln)
        else:
            roots.append(ln)

    out: List[ProductBomLine] = []

    def walk(nodes: List[ProductBomLine]) -> None:
        for ln in nodes:
            m = (ln.component_material_cd or "").strip()
            p = (ln.component_product_cd or "").strip()
            if m or p:
                out.append(ln)
            walk(children.get(ln.id, []))

    walk(roots)
    return out


async def _process_fee_increment_by_step(
    db: AsyncSession, product_cd: str, route_cd: str, target_date: date
) -> Tuple[Dict[int, Decimal], Dict[int, int]]:
    """line_type=process の増分のみを工程 step_no ごとに集計（部品・材料は BOM から別途）。"""
    conds = [
        ProductProcessUnitPrice.product_cd == product_cd,
        ProductProcessUnitPrice.route_cd == route_cd,
        ProductProcessUnitPrice.status == "active",
        or_(
            ProductProcessUnitPrice.line_type.is_(None),
            func.lower(ProductProcessUnitPrice.line_type) == "process",
        ),
    ]
    if target_date:
        conds.append(
            (ProductProcessUnitPrice.effective_from.is_(None)) | (ProductProcessUnitPrice.effective_from <= target_date)
        )
        conds.append(
            (ProductProcessUnitPrice.effective_to.is_(None)) | (ProductProcessUnitPrice.effective_to > target_date)
        )
    q = (
        select(ProductProcessUnitPrice)
        .where(*conds)
        .order_by(ProductProcessUnitPrice.step_no, ProductProcessUnitPrice.line_seq)
    )
    rows = (await db.execute(q)).scalars().all()
    fee_by_step: Dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    last_id_by_step: Dict[int, int] = {}
    for r in rows:
        st = int(r.step_no)
        fee_by_step[st] += r.increment_unit_price or Decimal("0")
        if r.id is not None:
            last_id_by_step[st] = r.id
    return fee_by_step, last_id_by_step


async def _build_cumulative_unit_price_by_step(
    db: AsyncSession,
    product_cd: str,
    route_cd: str,
    target_date: date,
    take_count: int,
) -> Tuple[Dict[int, Tuple[Decimal, Optional[int]]], int]:
    """
    各 step_no の「〜当工程完了時点」累計単価（材料投入 + 部品投入 + 加工費をルート順に積算）。
    未割当の材料・部品はフロント同様、各実工程の行には含めない。
    """
    steps = await _load_route_steps_ordered(db, product_cd, route_cd)
    if not steps:
        return {}, 0

    step_no_by_cd: Dict[str, int] = {}
    for s in steps:
        cd = (s.process_cd or "").strip()
        if cd:
            step_no_by_cd[cd] = int(s.step_no)

    fee_by_step, last_id_by_step = await _process_fee_increment_by_step(db, product_cd, route_cd, target_date)

    material_by_step: Dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    part_by_step: Dict[int, Decimal] = defaultdict(lambda: Decimal("0"))

    header_id = await _resolve_bom_header_id_for_valuation(db, product_cd)
    mat_map: Dict[str, Material] = {}
    part_map: Dict[str, PartMaster] = {}
    prod_map: Dict[str, Product] = {}

    if header_id:
        flat = await _flatten_bom_component_lines(db, header_id)
        mat_cds = {(ln.component_material_cd or "").strip() for ln in flat if (ln.component_material_cd or "").strip()}
        prd_cds = {(ln.component_product_cd or "").strip() for ln in flat if (ln.component_product_cd or "").strip()}
        if mat_cds:
            mq = select(Material).where(Material.material_cd.in_(mat_cds))
            for m in (await db.execute(mq)).scalars().all():
                mat_map[m.material_cd] = m
        if prd_cds:
            pq = select(PartMaster).where(PartMaster.part_cd.in_(prd_cds))
            for pt in (await db.execute(pq)).scalars().all():
                part_map[pt.part_cd] = pt
            prq = select(Product).where(Product.product_cd.in_(prd_cds))
            for pr in (await db.execute(prq)).scalars().all():
                prod_map[pr.product_cd] = pr

        for ln in flat:
            mat_cd = (ln.component_material_cd or "").strip()
            prd_cd = (ln.component_product_cd or "").strip()
            target_step: Optional[int] = None
            if ln.consume_step_no and int(ln.consume_step_no) > 0:
                target_step = int(ln.consume_step_no)
            elif (ln.consume_process_cd or "").strip():
                target_step = step_no_by_cd.get((ln.consume_process_cd or "").strip())

            if mat_cd:
                amt = _material_line_amount(ln, mat_map.get(mat_cd), take_count)
                if target_step is not None:
                    material_by_step[target_step] += amt
            elif prd_cd:
                amt = _part_line_amount(ln, part_map.get(prd_cd), prod_map.get(prd_cd))
                if target_step is not None:
                    part_by_step[target_step] += amt

    route_step_nos = [int(s.step_no) for s in steps]
    route_step_set = set(route_step_nos)
    # BOM の consume_step_no がルートに無い番号（例: ルート 10,20,30 に対し材料 15）でも
    # 数値順に積み上げないと当該材料が累計に一度も入らない。
    all_step_keys = sorted(
        route_step_set
        | set(material_by_step.keys())
        | set(part_by_step.keys())
        | set(fee_by_step.keys())
    )

    cum_by_step: Dict[int, Tuple[Decimal, Optional[int]]] = {}
    cum = Decimal("0")
    last_rule_id: Optional[int] = None
    max_step_no = max(route_step_nos) if route_step_nos else 0

    for st in all_step_keys:
        stage_inc = (
            material_by_step.get(st, Decimal("0"))
            + part_by_step.get(st, Decimal("0"))
            + fee_by_step.get(st, Decimal("0"))
        )
        cum += stage_inc
        rid = last_id_by_step.get(st)
        if rid is not None:
            last_rule_id = rid
        # 照会はルート上の工程 step_no のみ（inventory の process_cd 解決と一致）
        if st in route_step_set:
            cum_by_step[st] = (cum, last_rule_id)

    return cum_by_step, max_step_no


def _lookup_cumulative_price(
    cum_by_step: Dict[int, Tuple[Decimal, Optional[int]]],
    max_step_no: int,
    step_no: int,
) -> Tuple[Decimal, Optional[int]]:
    """step_no 完了時点の累計。step_no>=9999 は最終工程にフォールバック。"""
    if step_no in cum_by_step:
        return cum_by_step[step_no]
    if step_no >= 9999 and max_step_no and max_step_no in cum_by_step:
        return cum_by_step[max_step_no]
    return Decimal("0"), None


def _part_unit_price_for_inventory(part: PartMaster) -> Decimal:
    """部品単価：total_unit_price（DB 生成列）を優先。ORM で None のときは列の和で算出。"""
    tp = getattr(part, "total_unit_price", None)
    if tp is not None:
        try:
            return Decimal(str(tp))
        except Exception:
            pass
    u = part.unit_price
    m = part.material_unit_price
    return Decimal(str(u or 0)) + Decimal(str(m or 0))


def _pick_cumulative_from_snapshot_rows(
    snap_rows: List[ProductCostCumulativeSnapshot],
    process_cd: Optional[str],
    step_no: int,
) -> Optional[Decimal]:
    """最新スナップショット行から当該工程完了時点の cumulative_unit_price を取得。"""
    if not snap_rows:
        return None
    route_steps = [r for r in snap_rows if (r.row_kind or "") == "route_step"]
    if not route_steps:
        return None
    pc = (process_cd or "").strip()
    if pc:
        for r in route_steps:
            if (r.process_cd or "").strip() == pc:
                v = r.cumulative_unit_price
                return Decimal(str(v)) if v is not None else None
    if step_no >= 9999:
        with_step = [r for r in route_steps if r.step_no is not None]
        if not with_step:
            return None
        last = max(with_step, key=lambda x: int(x.step_no))
        v = last.cumulative_unit_price
        return Decimal(str(v)) if v is not None else None
    for r in route_steps:
        if r.step_no is not None and int(r.step_no) == int(step_no):
            v = r.cumulative_unit_price
            return Decimal(str(v)) if v is not None else None
    return None


async def _load_latest_snapshot_rows_for_pair(
    db: AsyncSession,
    product_cd: str,
    route_cd: str,
) -> List[ProductCostCumulativeSnapshot]:
    try:
        q = (
            select(ProductCostCumulativeSnapshot)
            .where(
                ProductCostCumulativeSnapshot.product_cd == product_cd,
                ProductCostCumulativeSnapshot.route_cd == route_cd,
                ProductCostCumulativeSnapshot.is_latest == 1,
            )
            .order_by(ProductCostCumulativeSnapshot.row_order)
        )
        return list((await db.execute(q)).scalars().all())
    except ProgrammingError:
        return []


async def _batch_latest_snapshots_for_details(
    db: AsyncSession, rows: List[InventoryValueCalcDetail]
) -> Dict[Tuple[str, str], List[ProductCostCumulativeSnapshot]]:
    """(product_cd, route_cd) ごとの最新スナップショット行を一括取得。"""
    pairs: List[Tuple[str, str]] = []
    seen: set[Tuple[str, str]] = set()
    for r in rows:
        if not r.product_cd or not r.route_cd:
            continue
        key = (r.product_cd, r.route_cd)
        if key not in seen:
            seen.add(key)
            pairs.append(key)
    if not pairs:
        return {}
    try:
        q = (
            select(ProductCostCumulativeSnapshot)
            .where(
                ProductCostCumulativeSnapshot.is_latest == 1,
                tuple_(ProductCostCumulativeSnapshot.product_cd, ProductCostCumulativeSnapshot.route_cd).in_(
                    pairs
                ),
            )
            .order_by(
                ProductCostCumulativeSnapshot.product_cd,
                ProductCostCumulativeSnapshot.route_cd,
                ProductCostCumulativeSnapshot.row_order,
            )
        )
        all_rows = list((await db.execute(q)).scalars().all())
    except ProgrammingError:
        return {}
    out: Dict[Tuple[str, str], List[ProductCostCumulativeSnapshot]] = {}
    for s in all_rows:
        k = (s.product_cd, s.route_cd)
        out.setdefault(k, []).append(s)
    return out


async def _batch_latest_snapshots_for_route_pairs(
    db: AsyncSession, pairs: List[Tuple[str, str]]
) -> Dict[Tuple[str, str], List[ProductCostCumulativeSnapshot]]:
    """(product_cd, route_cd) ごとの is_latest=1 スナップショット行（stock-panel 製品タブ用）。"""
    if not pairs:
        return {}
    try:
        q = (
            select(ProductCostCumulativeSnapshot)
            .where(
                ProductCostCumulativeSnapshot.is_latest == 1,
                tuple_(ProductCostCumulativeSnapshot.product_cd, ProductCostCumulativeSnapshot.route_cd).in_(
                    pairs
                ),
            )
            .order_by(
                ProductCostCumulativeSnapshot.product_cd,
                ProductCostCumulativeSnapshot.route_cd,
                ProductCostCumulativeSnapshot.row_order,
            )
        )
        all_rows = list((await db.execute(q)).scalars().all())
    except ProgrammingError:
        return {}
    out: Dict[Tuple[str, str], List[ProductCostCumulativeSnapshot]] = {}
    for s in all_rows:
        k = (s.product_cd, s.route_cd)
        out.setdefault(k, []).append(s)
    return out


async def _resolve_step_no(db: AsyncSession, product_cd: str, route_cd: str, process_cd: str) -> Optional[int]:
    """process_cd → step_no 解決"""
    q = select(ProductRouteStep.step_no).where(
        ProductRouteStep.product_cd == product_cd,
        ProductRouteStep.route_cd == route_cd,
        ProductRouteStep.process_cd == process_cd,
    ).limit(1)
    res = await db.execute(q)
    row = res.first()
    return row[0] if row else None


# ---------- 計算実行 ----------

@router.post("/calculate")
async def calculate_inventory_value(
    body: CalcRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """棚卸金額計算バッチ実行"""
    calc_date = date.today()
    start_dt = body.start_date
    end_dt = body.end_date

    run = InventoryValueCalcRun(
        calc_date=calc_date,
        start_date=start_dt,
        end_date=end_dt,
        process_cd=body.process_cd,
        status="running",
        executed_by=current_user.username if current_user else None,
    )
    db.add(run)
    await db.flush()

    log_sql = """
        SELECT id, product_cd, process_cd, item, quantity, log_date
        FROM inventory_logs
        WHERE log_date >= :start_date AND log_date <= :end_date
    """
    params: dict = {"start_date": start_dt, "end_date": end_dt}
    if body.process_cd:
        log_sql += " AND process_cd = :process_cd"
        params["process_cd"] = body.process_cd

    try:
        result = await db.execute(text(log_sql), params)
    except Exception:
        run.status = "failed"
        return {"success": False, "message": "inventory_logsテーブルの読み取りに失敗しました"}

    logs = result.fetchall()
    total_amount = Decimal("0")
    material_amount = Decimal("0")
    component_amount = Decimal("0")
    stay_amount = Decimal("0")
    total_rows = 0
    error_rows = 0

    product_cache: dict[str, Optional[Product]] = {}
    part_row_cache: dict[str, Optional[PartMaster]] = {}
    cumulative_map_cache: dict[tuple[str, str, str], Tuple[Dict[int, Tuple[Decimal, Optional[int]]], int]] = {}
    snapshot_rows_cache: dict[tuple[str, str], List[ProductCostCumulativeSnapshot]] = {}

    async def _get_cached_cumulative_map(
        p_cd: str, route: str, log_dt: date, take_ct: int
    ) -> Tuple[Dict[int, Tuple[Decimal, Optional[int]]], int]:
        dk = log_dt.isoformat()
        key = (p_cd, route, dk)
        if key not in cumulative_map_cache:
            cmap, mx = await _build_cumulative_unit_price_by_step(db, p_cd, route, log_dt, take_ct)
            cumulative_map_cache[key] = (cmap, mx)
        return cumulative_map_cache[key]

    async def _get_cached_snapshot_rows(p_cd: str, route: str) -> List[ProductCostCumulativeSnapshot]:
        sk = (p_cd, route)
        if sk not in snapshot_rows_cache:
            snapshot_rows_cache[sk] = await _load_latest_snapshot_rows_for_pair(db, p_cd, route)
        return snapshot_rows_cache[sk]

    for log in logs:
        total_rows += 1
        log_id = log[0]
        p_cd = log[1]
        proc_cd = log[2]
        item_type = log[3]
        qty = Decimal(str(log[4])) if log[4] else Decimal("0")
        log_date = log[5]
        if isinstance(log_date, str):
            try:
                log_date = datetime.strptime(log_date[:10], "%Y-%m-%d").date()
            except Exception:
                log_date = calc_date

        detail = InventoryValueCalcDetail(
            run_id=run.id,
            inventory_log_id=log_id,
            product_cd=p_cd,
            process_cd=proc_cd,
            item_type=item_type,
            quantity=qty,
        )

        # 部品：inventory_logs.product_cd を parts.part_cd とみなし、ルート・スナップショットは使わない
        if item_type and "部品" in item_type:
            p_key = (p_cd or "").strip()
            if p_key not in part_row_cache:
                part_q = select(PartMaster).where(PartMaster.part_cd == p_key)
                part_row_cache[p_key] = (await db.execute(part_q)).scalar_one_or_none()
            part_row = part_row_cache.get(p_key)
            if not part_row:
                detail.error_code = "NO_PART"
                detail.error_message = f"部品 {p_cd} が parts に存在しません"
                error_rows += 1
                db.add(detail)
                continue
            cum_price = _part_unit_price_for_inventory(part_row)
            if cum_price <= 0:
                detail.error_code = "NO_PRICE"
                detail.error_message = f"部品 {p_cd} の total_unit_price が未設定です"
                error_rows += 1
                db.add(detail)
                continue
            detail.unit_price_snapshot = cum_price
            detail.amount = qty * cum_price
            db.add(detail)
            component_amount += qty * cum_price
            total_amount += qty * cum_price
            continue

        if p_cd not in product_cache:
            pq = select(Product).where(Product.product_cd == p_cd)
            product_cache[p_cd] = (await db.execute(pq)).scalar_one_or_none()

        product = product_cache.get(p_cd)
        route_cd = product.route_cd if product and product.route_cd else None

        if not route_cd:
            detail.error_code = "NO_ROUTE"
            detail.error_message = f"製品 {p_cd} にデフォルトルートが未設定"
            error_rows += 1
            db.add(detail)
            continue

        detail.route_cd = route_cd
        step_no = await _resolve_step_no(db, p_cd, route_cd, proc_cd) if proc_cd else None

        if proc_cd and step_no is None:
            detail.error_code = "NO_STEP"
            detail.error_message = f"工程 {proc_cd} がルート {route_cd} に存在しません"
            error_rows += 1
            db.add(detail)
            continue

        if step_no is None:
            max_step_q = select(func.max(ProductRouteStep.step_no)).where(
                ProductRouteStep.product_cd == p_cd,
                ProductRouteStep.route_cd == route_cd,
            )
            max_step = (await db.execute(max_step_q)).scalar()
            step_no = max_step or 9999

        detail.step_no = step_no
        take_ct = int(product.take_count or 0) if product and product.take_count else 0
        snap_rows = await _get_cached_snapshot_rows(p_cd, route_cd)
        snap_cum = _pick_cumulative_from_snapshot_rows(snap_rows, proc_cd, int(step_no))
        cum_price = Decimal("0")
        rule_id: Optional[int] = None
        if snap_cum is not None and snap_cum > 0:
            cum_price = snap_cum
        else:
            cmap, mx_step = await _get_cached_cumulative_map(p_cd, route_cd, log_date, take_ct)
            cum_price, rule_id = _lookup_cumulative_price(cmap, mx_step, int(step_no))

        if cum_price == 0:
            detail.error_code = "NO_PRICE"
            detail.error_message = f"製品 {p_cd} ルート {route_cd} ステップ {step_no} の単価が未設定"
            error_rows += 1
            db.add(detail)
            continue

        amount = qty * cum_price
        detail.unit_price_snapshot = cum_price
        detail.amount = amount
        detail.price_rule_id = rule_id
        db.add(detail)

        if item_type and "材料" in item_type:
            material_amount += amount
        elif item_type and "部品" in item_type:
            component_amount += amount
        else:
            stay_amount += amount
        total_amount += amount

    run.total_amount = total_amount
    run.material_amount = material_amount
    run.component_amount = component_amount
    run.stay_amount = stay_amount
    run.total_rows = total_rows
    run.error_rows = error_rows
    run.status = "completed"

    return {
        "success": True,
        "data": {
            "run_id": run.id,
            "total_amount": float(total_amount),
            "material_amount": float(material_amount),
            "component_amount": float(component_amount),
            "stay_amount": float(stay_amount),
            "total_rows": total_rows,
            "error_rows": error_rows,
        },
    }


# ---------- 照会 ----------


@router.get("/stock-panel")
async def get_stock_panel(
    tab: str = Query(..., description="material | part | product"),
    as_of: str = Query(..., description="対象日（通常は対象月の月末） YYYY-MM-DD"),
    process_cd: Optional[str] = Query(None, description="製品タブのみ：工程CD（省略または all で倉庫在庫列）"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    sort_by: str = Query("product_name"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    棚卸金額管理画面用：実在庫テーブルから月末日の行を返す。
    - material: material_stock
    - part: part_stock
    - product: production_summarys の工程別 *_inventory 列
    """
    tab_norm = (tab or "").strip().lower()
    if tab_norm not in ("material", "part", "product"):
        raise HTTPException(status_code=422, detail="tab は material / part / product のいずれかを指定してください")
    as_of_d = _parse_as_of_date(as_of)
    desc_order = str(sort_order).strip().lower() == "desc"
    order_fn = desc if desc_order else asc

    def _material_order_col():
        # 材料の金額＝数量(current_stock) × 束重量(kg) × 単価
        material_amount_expr = (
            cast(MaterialStock.current_stock, Numeric)
            * func.coalesce(MaterialStock.bundle_weight, 0)
            * func.coalesce(MaterialStock.unit_price, 0)
        )
        m = {
            "product_name": MaterialStock.material_name,
            "product_cd": MaterialStock.material_cd,
            "quantity": MaterialStock.current_stock,
            "inventory_date": MaterialStock.date,
            "unit_price": MaterialStock.unit_price,
            "updated_at": MaterialStock.last_updated,
            "total_value": material_amount_expr,
        }
        return m.get(sort_by, MaterialStock.material_name)

    def _part_order_col():
        m = {
            "product_name": PartStock.part_name,
            "product_cd": PartStock.part_cd,
            "quantity": PartStock.current_stock,
            "inventory_date": PartStock.date,
            "unit_price": PartStock.unit_price,
            "updated_at": PartStock.last_updated,
            "total_value": cast(PartStock.current_stock, Numeric) * PartStock.unit_price,
            "kind": func.coalesce(PartMaster.kind, ""),
        }
        return m.get(sort_by, PartStock.part_name)

    try:
        if tab_norm == "material":
            base = select(MaterialStock).where(MaterialStock.date == as_of_d)
            cnt_q = select(func.count()).select_from(MaterialStock).where(MaterialStock.date == as_of_d)
            total = int((await db.execute(cnt_q)).scalar() or 0)
            sum_stmt = select(
                func.coalesce(
                    func.sum(
                        cast(MaterialStock.current_stock, Numeric)
                        * func.coalesce(MaterialStock.bundle_weight, 0)
                        * func.coalesce(MaterialStock.unit_price, 0)
                    ),
                    0,
                )
            ).where(MaterialStock.date == as_of_d)
            sum_scalar = (await db.execute(sum_stmt)).scalar()
            sum_total_value = round(float(sum_scalar or 0), 2)
            order_col = _material_order_col()
            q = base.order_by(order_fn(order_col)).offset((page - 1) * limit).limit(limit)
            rows = list((await db.execute(q)).scalars().all())
            out: List[dict] = []
            for r in rows:
                up = _fnum(r.unit_price)
                qty = int(r.current_stock or 0)
                bw = _fnum(r.bundle_weight)
                total_amt = round(float(qty) * bw * up, 2)
                out.append(
                    {
                        "id": r.id,
                        "stock_panel_row": True,
                        "item_type": "材料棚卸",
                        "product_cd": r.material_cd,
                        "product_name": r.material_name or r.material_cd,
                        "process_name": "材料",
                        "quantity": float(qty),
                        "unit": (r.unit or "") or "",
                        "unit_price": up,
                        "total_value": total_amt,
                        "inventory_date": str(r.date) if r.date else None,
                        "updated_at": str(r.last_updated) if r.last_updated else None,
                        "bundle_quantity": int(r.bundle_quantity or 0),
                        "bundle_weight": _fnum(r.bundle_weight),
                    }
                )
            return {
                "success": True,
                "data": {
                    "list": out,
                    "total": total,
                    "as_of": str(as_of_d),
                    "sum_total_value": sum_total_value,
                },
            }

        if tab_norm == "part":
            base = (
                select(PartStock, PartMaster.kind)
                .outerjoin(PartMaster, PartStock.part_cd == PartMaster.part_cd)
                .where(PartStock.date == as_of_d)
            )
            cnt_q = select(func.count()).select_from(PartStock).where(PartStock.date == as_of_d)
            total = int((await db.execute(cnt_q)).scalar() or 0)
            order_col = _part_order_col()
            q = base.order_by(order_fn(order_col)).offset((page - 1) * limit).limit(limit)
            rows = list((await db.execute(q)).all())
            out = []
            for row in rows:
                r = row[0]
                part_kind = row[1]
                up = _fnum(r.unit_price)
                qty = int(r.current_stock or 0)
                kind_str = (str(part_kind).strip() if part_kind is not None else "") or None
                out.append(
                    {
                        "id": r.id,
                        "stock_panel_row": True,
                        "item_type": "部品棚卸",
                        "product_cd": r.part_cd,
                        "product_name": r.part_name or r.part_cd,
                        "process_name": "部品",
                        "kind": kind_str,
                        "quantity": float(qty),
                        "unit": (r.unit or "") or "pcs",
                        "unit_price": up,
                        "total_value": round(qty * up, 2),
                        "inventory_date": str(r.date) if r.date else None,
                        "updated_at": str(r.last_updated) if r.last_updated else None,
                    }
                )
            return {"success": True, "data": {"list": out, "total": total, "as_of": str(as_of_d)}}

        # product
        inv_col_name = _inventory_col_for_process(process_cd)
        inv_col = getattr(ProductionSummary, inv_col_name)
        active_cd = (process_cd or "").strip() if process_cd and str(process_cd).strip().lower() != "all" else None
        if not active_cd:
            proc_display = "倉庫"
        else:
            pn = (
                await db.execute(select(Process.process_name).where(Process.process_cd == active_cd).limit(1))
            ).scalar_one_or_none()
            proc_display = pn or active_cd

        base = select(ProductionSummary).where(ProductionSummary.date == as_of_d)
        cnt_q = select(func.count()).select_from(ProductionSummary).where(ProductionSummary.date == as_of_d)
        # 工程指定時：当該製品×ルートにその工程が含まれる行のみ（ルートに無い製品は表示しない）
        if active_cd:
            in_route_for_process = exists(
                select(1)
                .select_from(ProductRouteStep)
                .where(
                    ProductRouteStep.product_cd == ProductionSummary.product_cd,
                    ProductRouteStep.route_cd == ProductionSummary.route_cd,
                    ProductRouteStep.process_cd == active_cd,
                )
            )
            base = base.where(in_route_for_process)
            cnt_q = cnt_q.where(in_route_for_process)

        total = int((await db.execute(cnt_q)).scalar() or 0)

        qty_order = inv_col
        order_map = {
            "product_name": ProductionSummary.product_name,
            "product_cd": ProductionSummary.product_cd,
            "quantity": inv_col,
            "inventory_date": ProductionSummary.date,
            "unit_price": ProductionSummary.product_cd,
            "total_value": inv_col,
            "updated_at": ProductionSummary.id,
        }
        order_col = order_map.get(sort_by, ProductionSummary.product_name)
        q = base.order_by(order_fn(order_col)).offset((page - 1) * limit).limit(limit)
        rows = list((await db.execute(q)).scalars().all())

        product_codes = sorted(
            {str(r.product_cd).strip() for r in rows if r.product_cd and str(r.product_cd).strip()}
        )
        product_kind_by_cd: Dict[str, Optional[str]] = {}
        if product_codes:
            pq = select(Product.product_cd, Product.kind).where(Product.product_cd.in_(product_codes))
            p_rows = list((await db.execute(pq)).all())
            for pcd, pk in p_rows:
                k = str(pcd or "").strip()
                if not k:
                    continue
                product_kind_by_cd[k] = (str(pk).strip() if pk is not None else "") or None

        pair_keys: List[Tuple[str, str]] = []
        seen_k: set[Tuple[str, str]] = set()
        for r in rows:
            if not r.product_cd or not r.route_cd:
                continue
            kk = (str(r.product_cd).strip(), str(r.route_cd).strip())
            if kk not in seen_k:
                seen_k.add(kk)
                pair_keys.append(kk)
        snap_by_pair = await _batch_latest_snapshots_for_route_pairs(db, pair_keys)

        out = []
        for r in rows:
            qty = int(getattr(r, inv_col_name) or 0)
            key = (str(r.product_cd or "").strip(), str(r.route_cd or "").strip())
            snap_rows = snap_by_pair.get(key, [])
            if active_cd:
                unit_dec = _pick_cumulative_from_snapshot_rows(snap_rows, active_cd, 0)
            else:
                unit_dec = _pick_cumulative_from_snapshot_rows(snap_rows, None, 9999)
            up = _fnum(unit_dec) if unit_dec is not None else None
            total_v: Optional[float]
            if up is not None:
                total_v = round(float(qty) * up, 2)
            else:
                total_v = None
            out.append(
                {
                    "id": r.id,
                    "stock_panel_row": True,
                    "item_type": "製品棚卸",
                    "product_cd": r.product_cd,
                    "product_name": r.product_name or r.product_cd,
                    "kind": product_kind_by_cd.get(str(r.product_cd or "").strip()),
                    "process_name": proc_display,
                    "process_cd": active_cd or "all",
                    "quantity": float(qty),
                    "unit": "pcs",
                    "unit_price": up,
                    "total_value": total_v,
                    "inventory_date": str(r.date) if r.date else None,
                    "updated_at": None,
                    "inventory_column": inv_col_name,
                    "route_cd": r.route_cd,
                }
            )
        return {
            "success": True,
            "data": {
                "list": out,
                "total": total,
                "as_of": str(as_of_d),
                "inventory_column": inv_col_name,
            },
        }
    except ProgrammingError as e:
        msg = str(e)
        if "material_stock" in msg.lower() and tab_norm == "material":
            raise HTTPException(status_code=503, detail="material_stock テーブルが利用できません") from e
        if "part_stock" in msg.lower() and tab_norm == "part":
            raise HTTPException(status_code=503, detail="part_stock テーブルが利用できません") from e
        raise HTTPException(status_code=503, detail="データベース参照に失敗しました") from e


@router.get("/summary")
async def get_value_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    process_cd: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """最新計算結果のサマリー"""
    q = select(InventoryValueCalcRun).order_by(InventoryValueCalcRun.id.desc())
    if process_cd:
        q = q.where(InventoryValueCalcRun.process_cd == process_cd)
    q = q.limit(1)
    run = (await db.execute(q)).scalar_one_or_none()
    if not run:
        return {
            "success": True,
            "data": {
                "total": {"total_amount": 0, "material_amount": 0, "component_amount": 0, "stay_amount": 0},
                "byType": [],
                "byProcess": [],
            },
        }

    detail_by_type_q = (
        select(
            InventoryValueCalcDetail.item_type,
            func.sum(InventoryValueCalcDetail.amount),
            func.sum(InventoryValueCalcDetail.quantity),
            func.count(),
        )
        .where(InventoryValueCalcDetail.run_id == run.id, InventoryValueCalcDetail.error_code.is_(None))
        .group_by(InventoryValueCalcDetail.item_type)
    )
    by_type_rows = (await db.execute(detail_by_type_q)).fetchall()

    detail_by_process_q = (
        select(
            InventoryValueCalcDetail.process_cd,
            func.sum(InventoryValueCalcDetail.amount),
            func.count(),
        )
        .where(InventoryValueCalcDetail.run_id == run.id, InventoryValueCalcDetail.error_code.is_(None))
        .group_by(InventoryValueCalcDetail.process_cd)
    )
    by_process_rows = (await db.execute(detail_by_process_q)).fetchall()

    return {
        "success": True,
        "data": {
            "run_id": run.id,
            "calc_date": str(run.calc_date),
            "total": {
                "total_amount": float(run.total_amount),
                "material_amount": float(run.material_amount),
                "component_amount": float(run.component_amount),
                "stay_amount": float(run.stay_amount),
            },
            "total_rows": run.total_rows,
            "error_rows": run.error_rows,
            "byType": [
                {"item_type": r[0], "amount": float(r[1] or 0), "quantity": float(r[2] or 0), "count": r[3]}
                for r in by_type_rows
            ],
            "byProcess": [
                {"process_cd": r[0], "amount": float(r[1] or 0), "count": r[2]}
                for r in by_process_rows
            ],
        },
    }


@router.get("/details")
async def get_value_details(
    run_id: Optional[int] = Query(None),
    item_type: Optional[str] = Query(None),
    process_cd: Optional[str] = Query(None),
    error_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """計算明細一覧"""
    if not run_id:
        latest = (
            await db.execute(select(InventoryValueCalcRun.id).order_by(InventoryValueCalcRun.id.desc()).limit(1))
        ).scalar()
        if not latest:
            return {"success": True, "data": {"list": [], "total": 0}}
        run_id = latest

    q = select(InventoryValueCalcDetail).where(InventoryValueCalcDetail.run_id == run_id)
    if item_type:
        q = q.where(InventoryValueCalcDetail.item_type == item_type)
    if process_cd:
        q = q.where(InventoryValueCalcDetail.process_cd == process_cd)
    if error_only:
        q = q.where(InventoryValueCalcDetail.error_code.isnot(None))

    cnt = await db.execute(select(func.count()).select_from(q.subquery()))
    total = cnt.scalar() or 0
    q = q.order_by(InventoryValueCalcDetail.id).offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    snap_by_pair = await _batch_latest_snapshots_for_details(db, list(rows))

    part_cds = [
        (r.product_cd or "").strip()
        for r in rows
        if (r.product_cd or "").strip() and r.item_type and "部品" in r.item_type
    ]
    part_by_cd: Dict[str, PartMaster] = {}
    if part_cds:
        pqs = select(PartMaster).where(PartMaster.part_cd.in_(list(set(part_cds))))
        for pr in (await db.execute(pqs)).scalars().all():
            if pr.part_cd:
                part_by_cd[(pr.part_cd or "").strip()] = pr

    list_payload: List[dict] = []
    for r in rows:
        is_component = bool(r.item_type and "部品" in r.item_type)
        pc_key = (r.product_cd or "").strip()
        part = part_by_cd.get(pc_key) if is_component else None
        product_name_pf: Optional[str] = (part.part_name if part and part.part_name else None) if is_component else None

        if r.error_code:
            unit_pf = float(r.unit_price_snapshot) if r.unit_price_snapshot is not None else None
        elif is_component and part:
            unit_pf = float(_part_unit_price_for_inventory(part))
        elif is_component:
            unit_pf = float(r.unit_price_snapshot) if r.unit_price_snapshot is not None else None
        else:
            pair_key = (r.product_cd, r.route_cd) if r.product_cd and r.route_cd else None
            snap_rows = snap_by_pair.get(pair_key, []) if pair_key else []
            snap_cum = _pick_cumulative_from_snapshot_rows(snap_rows, r.process_cd, int(r.step_no or 0))
            if snap_cum is not None and snap_cum > 0:
                unit_pf = float(snap_cum)
            else:
                unit_pf = float(r.unit_price_snapshot) if r.unit_price_snapshot is not None else None
        amt_pf = float(r.amount) if r.amount is not None else None
        row_dict: dict = {
            "id": r.id,
            "inventory_log_id": r.inventory_log_id,
            "product_cd": r.product_cd,
            "process_cd": r.process_cd,
            "item_type": r.item_type,
            "quantity": float(r.quantity) if r.quantity else 0,
            "route_cd": r.route_cd,
            "step_no": r.step_no,
            "unit_price": unit_pf,
            "amount": amt_pf,
            "error_code": r.error_code,
            "error_message": r.error_message,
        }
        if product_name_pf is not None:
            row_dict["product_name"] = product_name_pf
        list_payload.append(row_dict)

    return {
        "success": True,
        "data": {
            "list": list_payload,
            "total": total,
        },
    }


@router.get("/runs")
async def get_calc_runs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """計算バッチ履歴"""
    q = select(InventoryValueCalcRun).order_by(InventoryValueCalcRun.id.desc())
    cnt = await db.execute(select(func.count()).select_from(q.subquery()))
    total = cnt.scalar() or 0
    q = q.offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return {
        "success": True,
        "data": {
            "list": [
                {
                    "id": r.id,
                    "calc_date": str(r.calc_date),
                    "start_date": str(r.start_date) if r.start_date else None,
                    "end_date": str(r.end_date) if r.end_date else None,
                    "process_cd": r.process_cd,
                    "total_amount": float(r.total_amount),
                    "total_rows": r.total_rows,
                    "error_rows": r.error_rows,
                    "status": r.status,
                    "executed_by": r.executed_by,
                    "created_at": str(r.created_at) if r.created_at else None,
                }
                for r in rows
            ],
            "total": total,
        },
    }


@router.get("/errors")
async def get_errors(
    run_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """エラー一覧（未定価・ルート未設定等）"""
    if not run_id:
        latest = (
            await db.execute(select(InventoryValueCalcRun.id).order_by(InventoryValueCalcRun.id.desc()).limit(1))
        ).scalar()
        if not latest:
            return {"success": True, "data": []}
        run_id = latest

    q = (
        select(InventoryValueCalcDetail)
        .where(InventoryValueCalcDetail.run_id == run_id, InventoryValueCalcDetail.error_code.isnot(None))
        .order_by(InventoryValueCalcDetail.error_code, InventoryValueCalcDetail.product_cd)
    )
    rows = list((await db.execute(q)).scalars().all())
    unique_cds = sorted({(r.product_cd or "").strip() for r in rows if (r.product_cd or "").strip()})
    unique_proc = sorted({(r.process_cd or "").strip() for r in rows if (r.process_cd or "").strip()})

    product_names: Dict[str, str] = {}
    part_names: Dict[str, str] = {}
    material_names: Dict[str, str] = {}
    if unique_cds:
        pr = (await db.execute(select(Product.product_cd, Product.product_name).where(Product.product_cd.in_(unique_cds)))).all()
        for cd, nm in pr:
            if cd:
                product_names[str(cd).strip()] = (nm or cd or "").strip() or str(cd)
        par = (await db.execute(select(PartMaster.part_cd, PartMaster.part_name).where(PartMaster.part_cd.in_(unique_cds)))).all()
        for cd, nm in par:
            if cd:
                part_names[str(cd).strip()] = (nm or cd or "").strip() or str(cd)
        mat = (await db.execute(select(Material.material_cd, Material.material_name).where(Material.material_cd.in_(unique_cds)))).all()
        for cd, nm in mat:
            if cd:
                material_names[str(cd).strip()] = (nm or cd or "").strip() or str(cd)

    process_names: Dict[str, str] = {}
    if unique_proc:
        proc_rows = (
            await db.execute(select(Process.process_cd, Process.process_name).where(Process.process_cd.in_(unique_proc)))
        ).all()
        for cd, nm in proc_rows:
            if cd:
                process_names[str(cd).strip()] = (nm or cd or "").strip() or str(cd)

    def _error_row_display_name(r: InventoryValueCalcDetail) -> str:
        cd = (r.product_cd or "").strip()
        if not cd:
            return ""
        it = r.item_type or ""
        if "部品" in it:
            return part_names.get(cd) or product_names.get(cd) or cd
        if "材料" in it:
            return material_names.get(cd) or cd
        return product_names.get(cd) or part_names.get(cd) or cd

    def _error_row_process_name(r: InventoryValueCalcDetail) -> str:
        pcd = (r.process_cd or "").strip()
        if not pcd:
            return ""
        return process_names.get(pcd, pcd)

    return {
        "success": True,
        "data": [
            {
                "product_cd": r.product_cd,
                "product_name": _error_row_display_name(r),
                "process_cd": r.process_cd,
                "process_name": _error_row_process_name(r),
                "item_type": r.item_type,
                "error_code": r.error_code,
                "error_message": r.error_message,
            }
            for r in rows
        ],
    }


@router.get("/shipment-units")
async def get_shipment_units(
    date: Optional[str] = Query(None, description="対象日 (YYYY-MM-DD)"),
    dates: Optional[str] = Query(None, description="対象日（複数はカンマ区切り YYYY-MM-DD,YYYY-MM-DD）"),
    destination_cd: Optional[str] = Query(None, description="納入先コード"),
    destination_cds: Optional[str] = Query(
        None, description="納入先コード（複数はカンマ区切り CD1,CD2）"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """指定日(複数可)・納入先(複数可)の出荷確定本数を製品別に集計して返す"""
    date_inputs: List[str] = []
    if date:
        date_inputs.append(str(date).strip())
    if dates:
        date_inputs.extend([d.strip() for d in str(dates).split(",") if d.strip()])
    if not date_inputs:
        raise HTTPException(status_code=400, detail="date または dates は必須です")
    as_of_dates: List[date] = []
    for d in date_inputs:
        try:
            as_of_dates.append(datetime.strptime(d, "%Y-%m-%d").date())
        except ValueError:
            raise HTTPException(status_code=400, detail="date/dates は YYYY-MM-DD 形式で指定してください")
    as_of_dates = sorted(set(as_of_dates))

    dest_inputs: List[str] = []
    if destination_cd:
        dest_inputs.append(str(destination_cd).strip())
    if destination_cds:
        dest_inputs.extend([d.strip() for d in str(destination_cds).split(",") if d.strip()])
    destinations = sorted({d for d in dest_inputs if d})
    if not destinations:
        raise HTTPException(status_code=400, detail="destination_cd または destination_cds は必須です")

    q = (
        select(
            OrderDaily.product_cd,
            func.sum(OrderDaily.confirmed_units).label("confirmed_units_sum"),
        )
        .where(OrderDaily.date.in_(as_of_dates), OrderDaily.destination_cd.in_(destinations))
        .group_by(OrderDaily.product_cd)
    )
    rows = list((await db.execute(q)).all())

    return {
        "success": True,
        "data": {
            "list": [
                {
                    "product_cd": str(r.product_cd or "").strip(),
                    "confirmed_units_sum": int(r.confirmed_units_sum or 0),
                }
                for r in rows
                if str(r.product_cd or "").strip()
            ],
        },
    }


@router.get("/destinations")
async def get_destinations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """納入先一覧（ドロップダウン用）"""
    q = (
        select(Destination.destination_cd, Destination.destination_name)
        .where(Destination.status == 1)
        .order_by(Destination.destination_cd)
    )
    rows = list((await db.execute(q)).all())
    return {
        "success": True,
        "data": {
            "list": [
                {
                    "destination_cd": str(r.destination_cd or "").strip(),
                    "destination_name": str(r.destination_name or "").strip(),
                }
                for r in rows
                if str(r.destination_cd or "").strip()
            ],
        },
    }
