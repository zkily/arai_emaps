"""受注基準の工程別合計（order_monthly ＋ product_route_steps、月受注管理サマリーと同一ロジック）。"""
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.database.forming_plan_cascade import (
    SIMULATION_PROCESS_KEYS,
    molding_derived_plan_for_process,
)
from app.modules.erp.models import OrderDaily, OrderMonthly
from app.modules.master.models import ProductRouteStep

# 月受注サマリーと同じ process_cd 対応（外注検査は KT10 のみ）
ORDER_PROCESS_KEY_TO_KT_CD: dict[str, str | None] = {
    "molding": None,
    "cutting": "KT01",
    "chamfering": "KT02",
    "plating": "KT05",
    "outsourced_plating": "KT06",
    "welding": "KT07",
    "outsourced_welding": "KT08",
    "inspection": "KT09",
    "outsourced_warehouse": "KT10",
}


def order_monthly_base_where(om: type[OrderMonthly], year: int, month: int):
    """月受注管理 GET /monthly/summary と同一の除外条件。"""
    return and_(
        (om.product_name.is_(None)) | (~om.product_name.like("%加工%")),
        om.year == year,
        om.month == month,
    )


def months_in_period(ps: date, pe: date) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    y, m = ps.year, ps.month
    while (y, m) <= (pe.year, pe.month):
        out.append((y, m))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return out


async def load_product_process_cds(db: AsyncSession) -> dict[str, set[str]]:
    """product_route_steps：product_cd → 所持 process_cd 集合。"""
    q = select(ProductRouteStep.product_cd, ProductRouteStep.process_cd)
    res = await db.execute(q)
    out: dict[str, set[str]] = {}
    for product_cd, process_cd in res.all():
        cd = str(product_cd or "").strip()
        pc = str(process_cd or "").strip()
        if cd and pc:
            out.setdefault(cd, set()).add(pc)
    return out


async def _sum_forecast_units_for_month(
    db: AsyncSession,
    year: int,
    month: int,
    process_cd: str | None,
) -> int:
    om = OrderMonthly
    prs = ProductRouteStep
    base = order_monthly_base_where(om, year, month)
    q = select(func.coalesce(func.sum(om.forecast_units), 0)).select_from(om).where(base)
    if process_cd:
        subq = select(prs.product_cd).where(prs.process_cd == process_cd).distinct()
        q = q.where(om.product_cd.in_(subq))
    res = await db.execute(q)
    return int(res.scalar() or 0)


async def monthly_process_order_totals(db: AsyncSession, year: int, month: int) -> dict[str, int]:
    totals: dict[str, int] = {}
    for pk in SIMULATION_PROCESS_KEYS:
        kt = ORDER_PROCESS_KEY_TO_KT_CD.get(pk)
        totals[pk] = await _sum_forecast_units_for_month(db, year, month, kt)
    return totals


async def compute_order_process_totals_from_monthly(
    db: AsyncSession,
    ps: date,
    pe: date,
) -> list[dict[str, Any]]:
    """期間に含まれる各月の order_monthly.forecast_units を工程別に合算。"""
    totals_map: dict[str, int] = {pk: 0 for pk in SIMULATION_PROCESS_KEYS}
    for year, month in months_in_period(ps, pe):
        month_totals = await monthly_process_order_totals(db, year, month)
        for pk in SIMULATION_PROCESS_KEYS:
            totals_map[pk] += month_totals.get(pk, 0)

    molding_total = totals_map.get("molding", 0)
    out: list[dict[str, Any]] = []
    for pk in SIMULATION_PROCESS_KEYS:
        total = totals_map[pk]
        ratio = round(total / molding_total, 4) if molding_total > 0 else None
        out.append(
            {
                "process_key": pk,
                "total": total,
                "ratio_to_molding": ratio,
                "is_baseline": pk == "molding",
            }
        )
    return out


async def load_order_daily_by_product_date(
    db: AsyncSession,
    ps: date,
    pe: date,
) -> dict[str, dict[str, int]]:
    """order_daily：product_cd（末尾1正規化）× 日付 → 受注数（確定優先、無ければ内示）。"""
    od = OrderDaily
    norm_cd = func.concat(func.substr(od.product_cd, 1, func.length(od.product_cd) - 1), "1")
    q = (
        select(
            norm_cd.label("product_cd"),
            od.date,
            func.sum(func.coalesce(od.confirmed_units, 0)).label("confirmed"),
            func.sum(func.coalesce(od.forecast_units, 0)).label("forecast"),
        )
        .where(od.date >= ps, od.date <= pe)
        .group_by(norm_cd, od.date)
    )
    res = await db.execute(q)
    out: dict[str, dict[str, int]] = {}
    for row in res.all():
        cd = str(row.product_cd or "").strip()
        ds = row.date.isoformat() if row.date else ""
        if not cd or not ds:
            continue
        confirmed = int(row.confirmed or 0)
        forecast = int(row.forecast or 0)
        qty = confirmed if confirmed > 0 else forecast
        out.setdefault(cd, {})[ds] = qty
    return out


def build_order_matrix_rows(
    product_cds: list[str],
    dates: list[str],
    order_daily: dict[str, dict[str, int]],
    product_process_cds: dict[str, set[str]],
) -> list[dict[str, Any]]:
    """印刷用：order_daily の日別数量を product_route_steps 所属で各工程に配分。"""
    rows: list[dict[str, Any]] = []
    for product_cd in sorted(product_cds):
        pcds = product_process_cds.get(product_cd, set())
        daily = order_daily.get(product_cd, {})
        for pk in SIMULATION_PROCESS_KEYS:
            by_date: dict[str, int] = {}
            for d in dates:
                oq = daily.get(d, 0)
                by_date[d] = molding_derived_plan_for_process(oq, pk, pcds)
            rows.append({"product_cd": product_cd, "process_key": pk, "by_date": by_date})
    return rows
