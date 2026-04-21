"""
累計単価（工程完了時点）計算サービス

フロント ProductProcessUnitPriceEditor.vue の `cumulativeStageRows` と等価なロジックを
バックエンドに集約する。以下の正本データから累計単価の工程別内訳を構築する。

- 明細BOM（product_bom_headers / product_bom_lines）
- 材料マスタ（materials.unit_price / long_weight / single_price）
- 部品マスタ（parts：unit_price×exchange_rate + material_unit_price）
- 製品マスタ（products.unit_price, products.take_count）
- 工程別標準原価増分（product_process_unit_prices, line_type='process'）
- 製品別工程ルート（product_route_steps + processes.process_name）
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master.models import (
    Material,
    PartMaster,
    Process,
    Product,
    ProductBomHeader,
    ProductBomLine,
    ProductProcessUnitPrice,
    ProductRouteStep,
)


# ---------------------------------------------------------------------------
# UOM 判定（フロントと同じセマンティクス）
# ---------------------------------------------------------------------------

def _uom_norm(uom: Optional[str]) -> str:
    return (uom or "").strip().lower().replace(" ", "").replace("　", "")


def _uom_is_kg(uom: Optional[str]) -> bool:
    return _uom_norm(uom) in {"kg", "キロ", "ｋｇ", "kgs", "kilogram"}


def _uom_is_g(uom: Optional[str]) -> bool:
    return _uom_norm(uom) in {"g", "gr", "グラム", "ｇ"}


# ---------------------------------------------------------------------------
# マスタ取得ヘルパ
# ---------------------------------------------------------------------------

async def _load_parent_product(db: AsyncSession, product_cd: str) -> Optional[Product]:
    q = select(Product).where(Product.product_cd == product_cd)
    return (await db.execute(q)).scalar_one_or_none()


async def _load_active_bom_header(
    db: AsyncSession, product_cd: str, header_id: Optional[int]
) -> Optional[ProductBomHeader]:
    if header_id:
        h = await db.get(ProductBomHeader, header_id)
        if h and h.parent_product_cd == product_cd:
            return h
    q = (
        select(ProductBomHeader)
        .where(ProductBomHeader.parent_product_cd == product_cd)
        .order_by(
            (ProductBomHeader.status != "active").asc(),
            ProductBomHeader.id.desc(),
        )
    )
    return (await db.execute(q)).scalars().first()


async def _load_bom_lines(db: AsyncSession, header_id: int) -> list[ProductBomLine]:
    q = (
        select(ProductBomLine)
        .where(ProductBomLine.header_id == header_id)
        .order_by(ProductBomLine.line_no)
    )
    return list((await db.execute(q)).scalars().all())


async def _load_route_steps(
    db: AsyncSession, product_cd: str, route_cd: str
) -> list[dict]:
    q = (
        select(ProductRouteStep, Process.process_name)
        .outerjoin(Process, Process.process_cd == ProductRouteStep.process_cd)
        .where(
            ProductRouteStep.product_cd == product_cd,
            ProductRouteStep.route_cd == route_cd,
        )
        .order_by(ProductRouteStep.step_no)
    )
    rows = (await db.execute(q)).all()
    return [
        {
            "step_no": int(step.step_no),
            "process_cd": step.process_cd or "",
            "process_name": pname or step.process_cd or "",
        }
        for step, pname in rows
    ]


async def _load_process_fees(
    db: AsyncSession, product_cd: str, route_cd: str
) -> dict[int, Decimal]:
    """step_no → process 行 increment_unit_price 合計（active）"""
    q = select(ProductProcessUnitPrice).where(
        ProductProcessUnitPrice.product_cd == product_cd,
        ProductProcessUnitPrice.route_cd == route_cd,
        ProductProcessUnitPrice.status == "active",
    )
    rows = (await db.execute(q)).scalars().all()
    out: dict[int, Decimal] = {}
    for r in rows:
        if (r.line_type or "").lower() != "process":
            continue
        inc = r.increment_unit_price or Decimal("0")
        out[int(r.step_no)] = out.get(int(r.step_no), Decimal("0")) + inc
    return out


async def _load_materials_map(db: AsyncSession) -> dict[str, Material]:
    rows = (await db.execute(select(Material))).scalars().all()
    return {r.material_cd: r for r in rows if r.material_cd}


async def _load_parts_map(db: AsyncSession) -> dict[str, PartMaster]:
    rows = (await db.execute(select(PartMaster))).scalars().all()
    return {r.part_cd: r for r in rows if r.part_cd}


async def _load_products_map(db: AsyncSession) -> dict[str, Product]:
    rows = (await db.execute(select(Product))).scalars().all()
    return {r.product_cd: r for r in rows if r.product_cd}


# ---------------------------------------------------------------------------
# コアロジック
# ---------------------------------------------------------------------------

def _material_cost_for_line(
    line: ProductBomLine,
    material: Optional[Material],
    take_count: int,
) -> Decimal:
    """フロントの materialCostFromLine() と同じ金額を返す"""
    tc = Decimal(take_count) if take_count and take_count > 0 else Decimal(1)
    qty_per = Decimal(str(line.qty_per or 0))
    scrap = Decimal(str(line.scrap_rate or 0))
    qty_eff = qty_per * (Decimal(1) + scrap / Decimal(100))
    uom = line.uom or ""
    unit_price = Decimal(str((material.unit_price if material else None) or 0))
    long_w = Decimal(str((material.long_weight if material else None) or 0))
    single_p = Decimal(str((material.single_price if material else None) or 0))

    if _uom_is_kg(uom):
        return (qty_eff / tc) * unit_price
    if _uom_is_g(uom):
        kg = qty_eff / Decimal(1000)
        return (kg / tc) * unit_price
    if long_w > 0 and unit_price > 0:
        w = qty_eff * long_w
        return (w / tc) * unit_price
    if single_p > 0:
        return (qty_eff * single_p) / tc
    # fallback
    if long_w > 0 and unit_price > 0:
        return (qty_eff * long_w / tc) * unit_price
    return (qty_eff * unit_price) / tc


def _part_standard_jpy(part: Optional[PartMaster]) -> Decimal:
    if part is None:
        return Decimal(0)
    u = part.unit_price or Decimal(0)
    m = part.material_unit_price or Decimal(0)
    ex = part.exchange_rate
    if ex is not None and ex > 0:
        return Decimal(u) * Decimal(ex) + Decimal(m)
    return Decimal(u) + Decimal(m)


async def compute_cumulative_rows(
    db: AsyncSession,
    product_cd: str,
    route_cd: Optional[str] = None,
    bom_header_id: Optional[int] = None,
    preloaded: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """指定製品×ルートの累計単価行を返す

    戻り値:
        {
          "product_cd": ..., "route_cd": ..., "bom_header_id": ...,
          "rows": [ { row_kind, step_no, process_cd, stage_label,
                      material_increment, part_increment, process_increment,
                      stage_increment, cumulative_unit_price }, ... ],
          "errors": [ "...", ... ],
        }

    `preloaded` 提供 {"materials": {...}, "parts": {...}, "products": {...}} で
    バッチ処理時のマスタ再取得を避ける。
    """
    errors: list[str] = []

    product = await _load_parent_product(db, product_cd)
    if not product:
        return {
            "product_cd": product_cd,
            "route_cd": route_cd or "",
            "bom_header_id": None,
            "rows": [],
            "errors": [f"製品CD={product_cd} が products に存在しません"],
        }
    resolved_route_cd = (route_cd or product.route_cd or "").strip()
    if not resolved_route_cd:
        errors.append("ルートCDが特定できません（product.route_cd 未設定）")

    take_count_val = int(product.take_count) if product.take_count and int(product.take_count) > 0 else 1

    header = await _load_active_bom_header(db, product_cd, bom_header_id)
    bom_lines: list[ProductBomLine] = []
    if header:
        bom_lines = await _load_bom_lines(db, int(header.id))
    else:
        errors.append("BOMヘッダが見つかりません（材料/部品増分は 0 で計算）")

    steps = await _load_route_steps(db, product_cd, resolved_route_cd) if resolved_route_cd else []
    step_no_by_process_cd: dict[str, int] = {}
    for s in steps:
        if s["process_cd"]:
            step_no_by_process_cd[s["process_cd"]] = s["step_no"]

    fees = await _load_process_fees(db, product_cd, resolved_route_cd) if resolved_route_cd else {}

    materials_map: dict[str, Material]
    parts_map: dict[str, PartMaster]
    products_map: dict[str, Product]
    if preloaded and "materials" in preloaded and "parts" in preloaded and "products" in preloaded:
        materials_map = preloaded["materials"]
        parts_map = preloaded["parts"]
        products_map = preloaded["products"]
    else:
        materials_map = await _load_materials_map(db)
        parts_map = await _load_parts_map(db)
        products_map = await _load_products_map(db)

    # BOM 行を工程に振り分け
    material_cost_by_step: dict[int, Decimal] = {}
    part_cost_by_step: dict[int, Decimal] = {}
    unassigned_material = Decimal(0)
    unassigned_part = Decimal(0)

    for line in bom_lines:
        material_cd = (line.component_material_cd or "").strip()
        product_cd_child = (line.component_product_cd or "").strip()
        if not (material_cd or product_cd_child):
            continue

        # 消費工程の解決
        target_step: Optional[int] = None
        if line.consume_step_no is not None and int(line.consume_step_no) > 0:
            target_step = int(line.consume_step_no)
        elif line.consume_process_cd:
            target_step = step_no_by_process_cd.get(str(line.consume_process_cd).strip())

        if material_cd:
            mat = materials_map.get(material_cd)
            amount = _material_cost_for_line(line, mat, take_count_val)
            if target_step is None:
                unassigned_material += amount
            else:
                material_cost_by_step[target_step] = (
                    material_cost_by_step.get(target_step, Decimal(0)) + amount
                )
        else:
            qty_per = Decimal(str(line.qty_per or 0))
            scrap = Decimal(str(line.scrap_rate or 0))
            qty_eff = qty_per * (Decimal(1) + scrap / Decimal(100))
            part = parts_map.get(product_cd_child)
            part_up = _part_standard_jpy(part)
            if part_up <= 0:
                prod = products_map.get(product_cd_child)
                if prod and prod.unit_price:
                    part_up = Decimal(str(prod.unit_price))
            amount = qty_eff * part_up
            if target_step is None:
                unassigned_part += amount
            else:
                part_cost_by_step[target_step] = (
                    part_cost_by_step.get(target_step, Decimal(0)) + amount
                )

    # 行生成（工程順 + 未割当行）
    route_step_set = {s["step_no"] for s in steps}
    all_step_keys = sorted(
        route_step_set
        | set(material_cost_by_step.keys())
        | set(part_cost_by_step.keys())
        | set(fees.keys())
    )

    rows: list[dict[str, Any]] = []
    cumulative = Decimal(0)
    order = 0
    for st in all_step_keys:
        material_inc = material_cost_by_step.get(st, Decimal(0))
        part_inc = part_cost_by_step.get(st, Decimal(0))
        process_inc = fees.get(st, Decimal(0))
        stage_inc = material_inc + part_inc + process_inc
        cumulative += stage_inc
        if st not in route_step_set:
            continue
        s = next((x for x in steps if x["step_no"] == st), None)
        if not s:
            continue
        name = (s["process_name"] or s["process_cd"] or "").strip() or f"ステップ{st}"
        rows.append({
            "row_kind": "route_step",
            "row_order": order,
            "step_no": st,
            "process_cd": s["process_cd"] or None,
            "stage_label": f"〜 {name} 工程完了時点",
            "material_increment": material_inc,
            "part_increment": part_inc,
            "process_increment": process_inc,
            "stage_increment": stage_inc,
            "cumulative_unit_price": cumulative,
        })
        order += 1

    unassigned_stage = unassigned_material + unassigned_part
    if unassigned_stage > 0:
        cumulative += unassigned_stage
        rows.append({
            "row_kind": "unassigned",
            "row_order": order,
            "step_no": None,
            "process_cd": None,
            "stage_label": "〜 工程未割当の部品・材料投入",
            "material_increment": unassigned_material,
            "part_increment": unassigned_part,
            "process_increment": Decimal(0),
            "stage_increment": unassigned_stage,
            "cumulative_unit_price": cumulative,
        })

    return {
        "product_cd": product_cd,
        "route_cd": resolved_route_cd,
        "bom_header_id": int(header.id) if header else None,
        "rows": rows,
        "errors": errors,
    }


async def preload_all_masters(db: AsyncSession) -> dict[str, Any]:
    """バッチ処理時に一括で全マスタを載せる"""
    materials_map = await _load_materials_map(db)
    parts_map = await _load_parts_map(db)
    products_map = await _load_products_map(db)
    return {"materials": materials_map, "parts": parts_map, "products": products_map}
