"""
倉庫日次在庫 API
- POST /generate-data: 当月月初～3ヶ月後月末まで、全製品の日次行を生成（UPSERT）
- POST /sync-from-order-daily: order_daily + stock_transaction_logs + 倉庫在庫の日次繰り（carryover>0 の最終日から）
- GET  /rows: 指定期間・任意製品の一覧（page / pageSize でページネーション）
- GET  /product-options: products テーブルから製品 CD・名称（プルダウン用）
- GET  /shortage-print: shipping_warehouse_daily_stock の在庫マイナス行を印刷用 JSON で返す
"""
from __future__ import annotations

import calendar
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, asc, desc, func, or_, select, text
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.api import verify_token_and_get_user
from app.modules.auth.models import User
from app.modules.database.models import ProductionSummary
from app.modules.master.models import Destination, Product
from app.modules.shipping.warehouse_daily_stock_model import ShippingWarehouseDailyStock

logger = logging.getLogger(__name__)

router = APIRouter()

# Windows 等未安装 tzdata 时 ZoneInfo("Asia/Tokyo") 会失败，固定 UTC+9
JST = timezone(timedelta(hours=9), name="JST")

JP_WEEKDAY = ("月", "火", "水", "木", "金", "土", "日")


def _jst_today() -> date:
    return datetime.now(JST).date()


def _first_day_of_month(d: date) -> date:
    return date(d.year, d.month, 1)


def _last_day_of_month(y: int, m: int) -> date:
    last = calendar.monthrange(y, m)[1]
    return date(y, m, last)


def _add_months(y: int, m: int, delta: int) -> tuple[int, int]:
    """月 m（1–12）に delta を加えた (年, 月)。"""
    idx = (y * 12 + (m - 1)) + delta
    ny = idx // 12
    nm = idx % 12 + 1
    return ny, nm


def _generate_date_range_jst() -> tuple[date, date]:
    """
    当月月初 ～ 当月初日から数えて3ヶ月後の月の末日（含む）。
    例: 2026-04-26 実行 → 2026-04-01 ～ 2026-07-31
    """
    today = _jst_today()
    start = _first_day_of_month(today)
    ey, em = _add_months(start.year, start.month, 3)
    end = _last_day_of_month(ey, em)
    return start, end


def _jp_weekday(d: date) -> str:
    return JP_WEEKDAY[d.weekday()]


def _list_rows_order_by_product_name(sort_order: str) -> list[Any]:
    """一覧は製品名のみソート可（全件 ORDER BY + id で安定）。"""
    want_desc = (sort_order or "asc").strip().lower() == "desc"
    col = ShippingWarehouseDailyStock.product_name
    primary = desc(col) if want_desc else asc(col)
    return [primary, asc(ShippingWarehouseDailyStock.id)]


def _row_to_dict(
    r: ShippingWarehouseDailyStock,
    destination_name: Optional[str] = None,
    product_type: Optional[str] = None,
) -> dict[str, Any]:
    dn = (destination_name or "").strip()
    pt = (product_type or "").strip() if product_type is not None else ""
    return {
        "product_cd": r.product_cd,
        "product_name": r.product_name,
        "product_type": pt,
        "destination_cd": r.destination_cd,
        "destination_name": dn,
        "work_date": r.work_date.isoformat() if r.work_date else "",
        "weekday": r.weekday,
        "order_qty": float(r.order_qty or 0),
        "forecast_qty": float(r.forecast_qty or 0),
        "warehouse_carryover": float(r.warehouse_carryover or 0),
        "warehouse_actual": float(r.warehouse_actual or 0),
        "warehouse_defect": float(r.warehouse_defect or 0),
        "warehouse_disposal": float(r.warehouse_disposal or 0),
        "warehouse_hold": float(r.warehouse_hold or 0),
        "warehouse_stock": float(r.warehouse_stock or 0),
    }


@router.get("/rows")
async def list_rows_by_work_date(
    date_from: date = Query(..., description="開始日（YYYY-MM-DD）"),
    date_to: date = Query(..., description="終了日（YYYY-MM-DD）"),
    product_cd: Optional[str] = Query(None, description="製品CD（省略時は全製品）"),
    page: int = Query(1, ge=1, description="ページ番号（1 始まり）"),
    page_size: int = Query(100, ge=1, le=500, alias="pageSize", description="1 ページあたり件数"),
    sort_order: str = Query("asc", alias="sortOrder", description="製品名のみ：asc / desc（全件に対する順序）"),
    mass_product_only: bool = Query(
        False,
        alias="massProductOnly",
        description="true のとき products.product_type が「量産品」の行のみ（件数・一覧ともに適用）",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    if date_to < date_from:
        raise HTTPException(status_code=400, detail="date_to は date_from 以上である必要があります")
    conds = [
        ShippingWarehouseDailyStock.work_date >= date_from,
        ShippingWarehouseDailyStock.work_date <= date_to,
    ]
    pc = (product_cd or "").strip()
    if pc:
        conds.append(ShippingWarehouseDailyStock.product_cd == pc)
    # 製品名に「加工」を含む行は一覧・件数から除外
    conds.append(
        or_(
            ShippingWarehouseDailyStock.product_name.is_(None),
            ~ShippingWarehouseDailyStock.product_name.like("%加工%"),
        )
    )

    _collation = "utf8mb4_unicode_ci"
    join_product = (
        ShippingWarehouseDailyStock.product_cd.collate(_collation)
        == Product.product_cd.collate(_collation)
    )
    if mass_product_only:
        conds.append(Product.product_type == "量産品")

    count_stmt = (
        select(func.count())
        .select_from(ShippingWarehouseDailyStock)
        .outerjoin(Product, join_product)
        .where(*conds)
    )
    total = int((await db.execute(count_stmt)).scalar() or 0)

    order_by_list = _list_rows_order_by_product_name(sort_order)
    stmt = (
        select(ShippingWarehouseDailyStock, Destination.destination_name, Product.product_type)
        .outerjoin(
            Destination,
            (ShippingWarehouseDailyStock.destination_cd.collate("utf8mb4_unicode_ci"))
            == (Destination.destination_cd.collate("utf8mb4_unicode_ci")),
        )
        .outerjoin(Product, join_product)
        .where(*conds)
        .order_by(*order_by_list)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    res = await db.execute(stmt)
    rows = res.all()
    out_list = [_row_to_dict(stock, dn, pt) for stock, dn, pt in rows]
    return {
        "success": True,
        "data": {
            "list": out_list,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/product-options")
async def list_product_options_from_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """製品マスタテーブル products から、倉庫日次画面プルダウン用の一覧を返す。"""
    stmt = (
        select(Product.product_cd, Product.product_name)
        .where(Product.product_cd.isnot(None))
        .where(Product.product_cd != "")
        .where(
            or_(
                Product.product_name.is_(None),
                ~Product.product_name.like("%加工%"),
            )
        )
        .order_by(Product.product_cd)
    )
    res = await db.execute(stmt)
    out: list[dict[str, str]] = []
    for row in res.all():
        cd = (row[0] or "").strip()
        if not cd:
            continue
        out.append({"product_cd": cd, "product_name": (row[1] or "").strip()})
    return {"success": True, "data": {"list": out}}


@router.get("/shortage-print")
async def get_warehouse_daily_shortage_print(
    startDate: Optional[str] = Query(None, description="開始日 YYYY-MM-DD"),
    endDate: Optional[str] = Query(None, description="終了日 YYYY-MM-DD"),
    productCd: Optional[str] = Query(None, description="製品CD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    倉庫日次 shipping_warehouse_daily_stock の倉庫在庫（warehouse_stock）マイナス行を、
    GET /database/inventory-shortage-print と同形の JSON で返す（不足数発行・印刷用）。
    本数 = warehouse_stock。
    検査済在庫は production_summarys.inspection_inventory を同一製品CD・同一日付で集計（SUM）して付与。
    products.product_type が「量産品」の行のみ。
    """
    if not startDate or not endDate:
        return {"success": True, "data": []}
    try:
        start_d = date.fromisoformat(startDate)
        end_d = date.fromisoformat(endDate)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効な日付形式（YYYY-MM-DD）")

    _collation = "utf8mb4_unicode_ci"
    join_product = (
        ShippingWarehouseDailyStock.product_cd.collate(_collation)
        == Product.product_cd.collate(_collation)
    )
    join_dest_row = (
        ShippingWarehouseDailyStock.destination_cd.collate(_collation)
        == Destination.destination_cd.collate(_collation)
    )

    conds: list[Any] = [
        ShippingWarehouseDailyStock.work_date >= start_d,
        ShippingWarehouseDailyStock.work_date <= end_d,
        ShippingWarehouseDailyStock.warehouse_stock < 0,
        or_(
            ShippingWarehouseDailyStock.product_name.is_(None),
            ~ShippingWarehouseDailyStock.product_name.like("%加工%"),
        ),
    ]
    pc = (productCd or "").strip()
    if pc:
        conds.append(ShippingWarehouseDailyStock.product_cd == pc)
    conds.append(Product.product_type == "量産品")

    ps_insp_sq = (
        select(
            ProductionSummary.product_cd.label("ps_sum_cd"),
            ProductionSummary.date.label("ps_sum_dt"),
            func.coalesce(func.sum(ProductionSummary.inspection_inventory), 0).label("ps_inspection_sum"),
        )
        .group_by(ProductionSummary.product_cd, ProductionSummary.date)
        .subquery()
    )
    join_ps_insp = and_(
        ShippingWarehouseDailyStock.product_cd.collate(_collation) == ps_insp_sq.c.ps_sum_cd.collate(_collation),
        ShippingWarehouseDailyStock.work_date == ps_insp_sq.c.ps_sum_dt,
    )

    try:
        q = (
            select(
                ShippingWarehouseDailyStock.product_cd,
                ShippingWarehouseDailyStock.product_name,
                ShippingWarehouseDailyStock.work_date,
                ShippingWarehouseDailyStock.warehouse_stock,
                Product.product_type,
                Product.box_type,
                Product.unit_per_box,
                Destination.destination_name,
                ps_insp_sq.c.ps_inspection_sum,
            )
            .select_from(ShippingWarehouseDailyStock)
            .outerjoin(Product, join_product)
            .outerjoin(Destination, join_dest_row)
            .outerjoin(ps_insp_sq, join_ps_insp)
            .where(*conds)
            .order_by(
                ShippingWarehouseDailyStock.product_name,
                ShippingWarehouseDailyStock.product_cd,
                ShippingWarehouseDailyStock.work_date,
            )
        )
        result = await db.execute(q)
        rows = result.all()
        out: list[dict[str, Any]] = []
        for r in rows:
            try:
                raw_units = r.warehouse_stock
                units = int(raw_units) if raw_units is not None else 0
                raw_upb = r.unit_per_box
                unit_per_box = int(raw_upb) if raw_upb is not None and int(raw_upb) > 0 else None
                box_quantity = (units // unit_per_box) if unit_per_box else None
            except (TypeError, ValueError):
                units = 0
                unit_per_box = None
                box_quantity = None
            wd = r.work_date
            if wd is None:
                date_str = ""
            elif hasattr(wd, "isoformat"):
                date_str = wd.isoformat()
            else:
                date_str = str(wd)
            raw_insp = r.ps_inspection_sum
            try:
                inspection_inventory = int(raw_insp) if raw_insp is not None else None
            except (TypeError, ValueError):
                inspection_inventory = None

            out.append(
                {
                    "product_cd": r.product_cd or "",
                    "product_name": r.product_name or "",
                    "date": date_str,
                    "destination_name": (r.destination_name or "") if r.destination_name is not None else "",
                    "product_type": r.product_type or "",
                    "box_type": r.box_type or "",
                    "inspection_inventory": inspection_inventory,
                    "unit_per_box": r.unit_per_box,
                    "units": units,
                    "box_quantity": box_quantity,
                }
            )
        return {"success": True, "data": out}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("warehouse-daily shortage-print error: %s", e)
        raise HTTPException(status_code=500, detail=f"印刷データ取得エラー: {str(e)}")


_SYNC_ORDER_DAILY_SQL = """
UPDATE shipping_warehouse_daily_stock s
INNER JOIN (
  SELECT
    product_cd,
    destination_cd,
    `date` AS work_date,
    CAST(SUM(COALESCE(confirmed_units, 0)) AS DECIMAL(18,2)) AS order_qty,
    CAST(SUM(COALESCE(forecast_units, 0)) AS DECIMAL(18,2)) AS forecast_qty
  FROM order_daily
  WHERE product_cd IS NOT NULL AND product_cd <> ''
    AND destination_cd IS NOT NULL AND destination_cd <> ''
  GROUP BY product_cd, destination_cd, `date`
) od ON (s.product_cd COLLATE utf8mb4_unicode_ci) = (od.product_cd COLLATE utf8mb4_unicode_ci)
  AND (s.destination_cd COLLATE utf8mb4_unicode_ci) = (od.destination_cd COLLATE utf8mb4_unicode_ci)
  AND s.work_date = od.work_date
SET
  s.order_qty = od.order_qty,
  s.forecast_qty = od.forecast_qty
"""

# stock_transaction_logs: 品目=製品、日付=DATE(transaction_time)、target_cd=製品CD。
# shipping に納入先が無いため、同一製品×日の集計値を当該 product_cd+work_date の全 destination 行へ反映する。
_STL_AGG_BASE = """
SELECT
  DATE(stl.transaction_time) AS d,
  stl.target_cd AS product_cd,
  CAST(SUM(COALESCE(stl.quantity, 0)) AS DECIMAL(18,2)) AS qty
FROM stock_transaction_logs stl
WHERE stl.stock_type = '製品'
  AND stl.transaction_type = :tt
  AND stl.target_cd IS NOT NULL AND stl.target_cd <> ''
  AND stl.transaction_time IS NOT NULL
GROUP BY DATE(stl.transaction_time), stl.target_cd
"""

# warehouse_actual = 同一日・同一 target_cd で SUM(入庫 quantity) − SUM(出庫 quantity)
_SYNC_STL_WAREHOUSE_ACTUAL = """
UPDATE shipping_warehouse_daily_stock s
INNER JOIN (
  SELECT
    DATE(stl.transaction_time) AS d,
    stl.target_cd AS product_cd,
    CAST(
      SUM(CASE WHEN stl.transaction_type = '入庫' THEN COALESCE(stl.quantity, 0) ELSE 0 END)
      - SUM(CASE WHEN stl.transaction_type = '出庫' THEN COALESCE(stl.quantity, 0) ELSE 0 END)
    AS DECIMAL(18,2)) AS qty
  FROM stock_transaction_logs stl
  WHERE stl.stock_type = '製品'
    AND stl.transaction_type IN ('入庫', '出庫')
    AND stl.target_cd IS NOT NULL AND stl.target_cd <> ''
    AND stl.transaction_time IS NOT NULL
  GROUP BY DATE(stl.transaction_time), stl.target_cd
) agg ON s.work_date = agg.d
  AND (s.product_cd COLLATE utf8mb4_unicode_ci) = (agg.product_cd COLLATE utf8mb4_unicode_ci)
SET s.warehouse_actual = agg.qty
"""

_SYNC_STL_WAREHOUSE_CARRYOVER = f"""
UPDATE shipping_warehouse_daily_stock s
INNER JOIN ({_STL_AGG_BASE}) agg ON s.work_date = agg.d
  AND (s.product_cd COLLATE utf8mb4_unicode_ci) = (agg.product_cd COLLATE utf8mb4_unicode_ci)
SET s.warehouse_carryover = agg.qty
"""

_SYNC_STL_WAREHOUSE_DEFECT = f"""
UPDATE shipping_warehouse_daily_stock s
INNER JOIN ({_STL_AGG_BASE}) agg ON s.work_date = agg.d
  AND (s.product_cd COLLATE utf8mb4_unicode_ci) = (agg.product_cd COLLATE utf8mb4_unicode_ci)
SET s.warehouse_defect = agg.qty
"""

_SYNC_STL_WAREHOUSE_DISPOSAL = f"""
UPDATE shipping_warehouse_daily_stock s
INNER JOIN ({_STL_AGG_BASE}) agg ON s.work_date = agg.d
  AND (s.product_cd COLLATE utf8mb4_unicode_ci) = (agg.product_cd COLLATE utf8mb4_unicode_ci)
SET s.warehouse_disposal = agg.qty
"""

_SYNC_STL_WAREHOUSE_HOLD = f"""
UPDATE shipping_warehouse_daily_stock s
INNER JOIN ({_STL_AGG_BASE}) agg ON s.work_date = agg.d
  AND (s.product_cd COLLATE utf8mb4_unicode_ci) = (agg.product_cd COLLATE utf8mb4_unicode_ci)
SET s.warehouse_hold = agg.qty
"""

# 同一製品×納入先で日付昇順に、前日の warehouse_stock を足し込む。
# warehouse_stock = carryover + actual - defect - disposal - forecast_qty + 前日 warehouse_stock
_ROLL_WAREHOUSE_STOCK_ONE_DAY = """
UPDATE shipping_warehouse_daily_stock s
LEFT JOIN shipping_warehouse_daily_stock p ON
  (p.product_cd COLLATE utf8mb4_unicode_ci) = (s.product_cd COLLATE utf8mb4_unicode_ci)
  AND (p.destination_cd COLLATE utf8mb4_unicode_ci) = (s.destination_cd COLLATE utf8mb4_unicode_ci)
  AND p.work_date = DATE_SUB(s.work_date, INTERVAL 1 DAY)
SET s.warehouse_stock = CAST(
  COALESCE(s.warehouse_carryover, 0)
  + COALESCE(s.warehouse_actual, 0)
  - COALESCE(s.warehouse_defect, 0)
  - COALESCE(s.warehouse_disposal, 0)
  - COALESCE(s.forecast_qty, 0)
  + COALESCE(p.warehouse_stock, 0)
AS DECIMAL(18,2))
WHERE s.work_date = :wd
"""


async def _roll_warehouse_stock_from_last_positive_carryover(db: AsyncSession) -> tuple[date | None, int]:
    """
    テーブル全体で warehouse_carryover > 0 のうち最も遅い work_date を開始日とし、
    その日からテーブル内最大 work_date まで、日付順に warehouse_stock を再計算する。
    該当行が無い場合は何もしない。
    """
    start_res = await db.execute(
        text("SELECT MAX(work_date) AS d FROM shipping_warehouse_daily_stock WHERE warehouse_carryover > 0")
    )
    start = start_res.scalar()
    if start is None:
        return None, 0
    end_res = await db.execute(text("SELECT MAX(work_date) AS d FROM shipping_warehouse_daily_stock"))
    end = end_res.scalar()
    if end is None or end < start:
        return start, 0
    n_days = 0
    d = start
    while d <= end:
        await db.execute(text(_ROLL_WAREHOUSE_STOCK_ONE_DAY), {"wd": d})
        n_days += 1
        d += timedelta(days=1)
    return start, n_days


@router.post("/sync-from-order-daily")
async def sync_from_order_daily(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    1) order_daily を product_cd + destination_cd + date で集約し、
       shipping_warehouse_daily_stock の order_qty / forecast_qty を更新。
    2) stock_transaction_logs（stock_type=製品）を DATE(transaction_time)+target_cd で集約し、
       transaction_type=初期 → warehouse_carryover、
       warehouse_actual = SUM(入庫 quantity) − SUM(出庫 quantity)、
       不良 / 廃棄 / 保留 → warehouse_defect / warehouse_disposal / warehouse_hold。
    3) warehouse_carryover > 0 が存在する最遅の work_date を開始日とし、当該日～テーブル最大日まで
       日付順に warehouse_stock を再計算（製品×納入先ごとに前日の warehouse_stock を加算）。
       式: carryover + actual - defect - disposal - forecast_qty + 前日 warehouse_stock。
    """
    result_od = await db.execute(text(_SYNC_ORDER_DAILY_SQL))
    n_od = result_od.rowcount if result_od.rowcount is not None else -1

    result_co = await db.execute(text(_SYNC_STL_WAREHOUSE_CARRYOVER), {"tt": "初期"})
    n_co = result_co.rowcount if result_co.rowcount is not None else -1
    result_a = await db.execute(text(_SYNC_STL_WAREHOUSE_ACTUAL))
    n_a = result_a.rowcount if result_a.rowcount is not None else -1
    result_de = await db.execute(text(_SYNC_STL_WAREHOUSE_DEFECT), {"tt": "不良"})
    n_de = result_de.rowcount if result_de.rowcount is not None else -1
    result_di = await db.execute(text(_SYNC_STL_WAREHOUSE_DISPOSAL), {"tt": "廃棄"})
    n_di = result_di.rowcount if result_di.rowcount is not None else -1
    result_ho = await db.execute(text(_SYNC_STL_WAREHOUSE_HOLD), {"tt": "保留"})
    n_ho = result_ho.rowcount if result_ho.rowcount is not None else -1

    roll_start, roll_days = await _roll_warehouse_stock_from_last_positive_carryover(db)

    logger.info(
        "warehouse_daily sync-from-order-daily user=%s od=%s stl_carryover=%s stl_actual=%s defect=%s disposal=%s hold=%s stock_roll_start=%s stock_roll_days=%s",
        getattr(current_user, "username", None),
        n_od,
        n_co,
        n_a,
        n_de,
        n_di,
        n_ho,
        roll_start,
        roll_days,
    )
    return {
        "success": True,
        "data": {
            "order_daily_rows": n_od,
            "stock_carryover_rows": n_co,
            "stock_actual_rows": n_a,
            "stock_defect_rows": n_de,
            "stock_disposal_rows": n_di,
            "stock_hold_rows": n_ho,
            "warehouse_stock_roll_start": roll_start.isoformat() if roll_start else None,
            "warehouse_stock_roll_days": roll_days,
            "rows_matched": n_od,
        },
        "message": "order_daily と在庫履歴から更新しました",
    }


@router.post("/generate-data")
async def generate_warehouse_daily_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_token_and_get_user),
):
    """
    当月月初から「+3ヶ月後の月」の末日まで、products 全件 × 全日付の行を
    shipping_warehouse_daily_stock に UPSERT する。
    weekday は work_date（JST 暦）から自動（月…日）。
    数量系は 0。destination_cd が NULL/空のときは N01。
    """
    start, end = _generate_date_range_jst()
    days: List[date] = []
    d = start
    while d <= end:
        days.append(d)
        d += timedelta(days=1)

    prod_res = await db.execute(
        select(Product.product_cd, Product.product_name, Product.destination_cd).order_by(Product.product_cd)
    )
    products = prod_res.all()
    if not products:
        raise HTTPException(status_code=400, detail="製品マスタ（products）にデータがありません")

    zero = Decimal("0")
    payload: list[dict[str, Any]] = []
    for wd in days:
        wk = _jp_weekday(wd)
        for row in products:
            pcd = (row.product_cd or "").strip()
            if not pcd:
                continue
            pname = (row.product_name or "").strip() or pcd
            dest = (row.destination_cd or "").strip() or "N01"
            payload.append(
                {
                    "product_cd": pcd,
                    "product_name": pname[:255],
                    "destination_cd": dest[:50],
                    "work_date": wd,
                    "weekday": wk,
                    "order_qty": zero,
                    "forecast_qty": zero,
                    "warehouse_carryover": zero,
                    "warehouse_actual": zero,
                    "warehouse_defect": zero,
                    "warehouse_disposal": zero,
                    "warehouse_hold": zero,
                    "warehouse_stock": zero,
                }
            )

    total = len(payload)
    if total == 0:
        raise HTTPException(status_code=400, detail="生成対象行がありません")

    chunk_size = 400
    for i in range(0, total, chunk_size):
        chunk = payload[i : i + chunk_size]
        stmt = mysql_insert(ShippingWarehouseDailyStock).values(chunk)
        stmt = stmt.on_duplicate_key_update(
            product_name=stmt.inserted.product_name,
            weekday=stmt.inserted.weekday,
        )
        await db.execute(stmt)
        await db.commit()

    sample: list[str] = []
    for row in products[:2]:
        pcd = (row.product_cd or "").strip()
        if not pcd:
            continue
        dest = (row.destination_cd or "").strip() or "N01"
        pname = (row.product_name or "").strip() or pcd
        ds = days[0].strftime("%Y/%m/%d")
        sample.append(f"{pcd} {pname} {ds} {dest}")
        if len(sample) >= 2:
            break

    logger.info(
        "warehouse_daily generate-data user=%s rows=%s range=%s..%s",
        getattr(current_user, "username", None),
        total,
        start,
        end,
    )

    return {
        "success": True,
        "data": {
            "inserted_or_updated": total,
            "date_from": start.isoformat(),
            "date_to": end.isoformat(),
            "day_count": len(days),
            "product_count": len(products),
            "sample_lines": sample,
        },
        "message": "データを生成しました",
    }
