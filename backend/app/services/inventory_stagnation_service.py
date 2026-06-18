"""在庫停滞検知（production_summarys *_inventory 列）"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.database.models import ProductionSummary

INVENTORY_COLUMNS = [
    "cutting_inventory",
    "chamfering_inventory",
    "molding_inventory",
    "plating_inventory",
    "welding_inventory",
    "inspection_inventory",
    "warehouse_inventory",
    "outsourced_warehouse_inventory",
    "outsourced_plating_inventory",
    "outsourced_welding_inventory",
    "pre_welding_inspection_inventory",
    "pre_inspection_inventory",
    "pre_outsourcing_inventory",
]

INVENTORY_COLUMN_LABELS: dict[str, str] = {
    "cutting_inventory": "切断",
    "chamfering_inventory": "面取",
    "molding_inventory": "成型",
    "plating_inventory": "メッキ",
    "welding_inventory": "溶接",
    "inspection_inventory": "検査",
    "warehouse_inventory": "倉庫",
    "outsourced_warehouse_inventory": "外注倉庫",
    "outsourced_plating_inventory": "外注メッキ",
    "outsourced_welding_inventory": "外注溶接",
    "pre_welding_inspection_inventory": "溶接前検査",
    "pre_inspection_inventory": "外注支給前",
    "pre_outsourcing_inventory": "外注検査前",
}


def inventory_column_label(col: str) -> str:
    return INVENTORY_COLUMN_LABELS.get(col, col)


def parse_as_of_date(as_of: str | None) -> date:
    if as_of and as_of.strip():
        return date.fromisoformat(as_of.strip()[:10])
    return now_jst().date()


async def fetch_inventory_stagnation_hits(
    db: AsyncSession,
    *,
    as_of: str | None = None,
    min_quantity: int = 50,
    stable_calendar_days: int = 7,
    product_cd: str | None = None,
    keyword: str | None = None,
) -> dict:
    """在庫停滞検知。api と通知サービスから共用。"""
    as_of_d = parse_as_of_date(as_of)
    window_days = int(stable_calendar_days)
    start_d = as_of_d - timedelta(days=window_days - 1)
    required_dates = [start_d + timedelta(days=i) for i in range(window_days)]

    inventory_attrs = [getattr(ProductionSummary, c) for c in INVENTORY_COLUMNS]
    q = select(
        ProductionSummary.product_cd,
        ProductionSummary.product_name,
        ProductionSummary.route_cd,
        ProductionSummary.date,
        *inventory_attrs,
    ).where(
        and_(
            ProductionSummary.date >= start_d,
            ProductionSummary.date <= as_of_d,
            ProductionSummary.product_cd.isnot(None),
            ProductionSummary.product_cd != "",
        )
    )
    if product_cd and product_cd.strip():
        q = q.where(ProductionSummary.product_cd == product_cd.strip())
    if keyword and keyword.strip():
        k = f"%{keyword.strip()}%"
        q = q.where(
            or_(
                ProductionSummary.product_name.ilike(k),
                ProductionSummary.product_cd.ilike(k),
            )
        )
    q = q.order_by(
        ProductionSummary.product_cd,
        ProductionSummary.route_cd,
        ProductionSummary.date,
    )
    rows = (await db.execute(q)).all()

    buckets: dict[tuple, dict] = {}
    for r in rows:
        pcd = (r.product_cd or "").strip()
        rcd = (r.route_cd or "").strip()
        if not pcd:
            continue
        key = (pcd, rcd)
        entry = buckets.get(key)
        if entry is None:
            entry = {
                "product_cd": pcd,
                "product_name": r.product_name or "",
                "route_cd": rcd,
                "rows_by_date": {},
            }
            buckets[key] = entry
        d = r.date
        if isinstance(d, str):
            try:
                d = date.fromisoformat(d[:10])
            except ValueError:
                continue
        entry["rows_by_date"][d] = r
        if not entry["product_name"] and r.product_name:
            entry["product_name"] = r.product_name

    hits: list[dict] = []
    for entry in buckets.values():
        rows_by_date = entry["rows_by_date"]
        if not all(d in rows_by_date for d in required_dates):
            continue
        ordered = [rows_by_date[d] for d in required_dates]
        for col in INVENTORY_COLUMNS:
            values = [getattr(row, col) for row in ordered]
            if all(v is None for v in values):
                continue
            normalized = [0 if v is None else int(v) for v in values]
            v0 = normalized[0]
            if any(v != v0 for v in normalized):
                continue
            if v0 <= min_quantity:
                continue
            hits.append(
                {
                    "product_cd": entry["product_cd"],
                    "product_name": entry["product_name"],
                    "route_cd": entry["route_cd"],
                    "inventory_column": col,
                    "inventory_column_label": inventory_column_label(col),
                    "stable_quantity": v0,
                    "period_start": required_dates[0].isoformat(),
                    "period_end": required_dates[-1].isoformat(),
                    "days": window_days,
                }
            )

    hits.sort(
        key=lambda x: (
            -x["stable_quantity"],
            x["product_name"] or "",
            x["product_cd"],
            x["route_cd"],
            x["inventory_column"],
        )
    )

    return {
        "list": hits,
        "total": len(hits),
        "as_of": as_of_d.isoformat(),
        "period_start": start_d.isoformat(),
        "period_end": as_of_d.isoformat(),
        "min_quantity": int(min_quantity),
        "stable_calendar_days": window_days,
    }
