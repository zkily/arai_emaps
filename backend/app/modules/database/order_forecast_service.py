"""基于 order_daily / order_monthly 推算下月、下下月日别订单。"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.erp.models import OrderDaily, OrderMonthly
from app.modules.order.generate_daily_service import build_working_days_cache

WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def _normalize_product_cd(product_cd: str) -> str:
    s = (product_cd or "").strip()
    if len(s) >= 2:
        return s[:-1] + "1"
    return s


def _add_months(y: int, m: int, delta: int) -> tuple[int, int]:
    total = y * 12 + (m - 1) + delta
    return total // 12, total % 12 + 1


def _month_bounds(y: int, m: int) -> tuple[date, date]:
    last = monthrange(y, m)[1]
    return date(y, m, 1), date(y, m, last)


def _distribute_forecast(work_days: list[date], total: int) -> list[tuple[date, int]]:
    if not work_days or total <= 0:
        return [(d, 0) for d in work_days]
    if total < 1100:
        per_day = [0] * len(work_days)
        if len(work_days) >= 3:
            per_day[2] = total
        else:
            per_day[0] = total
    else:
        base, rem = divmod(total, len(work_days))
        per_day = [base] * len(work_days)
        for i in range(rem):
            per_day[-(1 + i)] += 1
    return list(zip(work_days, per_day))


async def _monthly_total_from_db(
    db: AsyncSession,
    year: int,
    month: int,
    product_cd: str | None,
) -> tuple[int, str]:
    """返回 (forecast_units 合计, source)。"""
    om = OrderMonthly
    q = select(func.coalesce(func.sum(om.forecast_units), 0)).where(
        and_(om.year == year, om.month == month, om.product_type == "量産品")
    )
    if product_cd:
        q = q.where(om.product_cd == _normalize_product_cd(product_cd))
    res = await db.execute(q)
    total = int(res.scalar() or 0)
    if total > 0:
        return total, "order_monthly"

    # 最近 3 个月 confirmed_units 月均
    od = OrderDaily
    end_d = date(year, month, 1) - timedelta(days=1)
    start_d = date(end_d.year, end_d.month, 1)
    for _ in range(2):
        start_d = date(start_d.year, start_d.month, 1) - timedelta(days=1)
        start_d = date(start_d.year, start_d.month, 1)

    norm_cd = func.concat(func.substr(od.product_cd, 1, func.length(od.product_cd) - 1), "1")
    q2 = select(func.coalesce(func.sum(od.confirmed_units), 0)).where(
        and_(od.date >= start_d, od.date <= end_d)
    )
    if product_cd:
        q2 = q2.where(norm_cd == _normalize_product_cd(product_cd))
    res2 = await db.execute(q2)
    hist_total = int(res2.scalar() or 0)
    if hist_total > 0:
        return hist_total // 3, "historical_avg"
    return 0, "pattern_only"


async def _destinations_for_product(db: AsyncSession, product_cd: str | None) -> list[str]:
    od = OrderDaily
    q = select(od.destination_cd).distinct()
    if product_cd:
        norm = func.concat(func.substr(od.product_cd, 1, func.length(od.product_cd) - 1), "1")
        q = q.where(norm == _normalize_product_cd(product_cd))
    res = await db.execute(q)
    return [r[0] for r in res.all() if r[0]]


async def build_order_forecast(
    db: AsyncSession,
    base_month: str,
    months: int = 2,
    product_cd: str | None = None,
) -> list[dict[str, Any]]:
    """
    base_month: YYYY-MM
    返回 M+1 … M+months 的推算结果列表。
    """
    parts = (base_month or "").strip().split("-")
    if len(parts) != 2:
        return []
    base_y, base_m = int(parts[0]), int(parts[1])

    dest_cds = await _destinations_for_product(db, product_cd)
    if not dest_cds:
        dest_cds = ["DEFAULT"]

    results: list[dict[str, Any]] = []
    for offset in range(1, months + 1):
        ty, tm = _add_months(base_y, base_m, offset)
        first, last = _month_bounds(ty, tm)
        forecast_total, source = await _monthly_total_from_db(db, ty, tm, product_cd)

        workdays_cache = await build_working_days_cache(db, first, last, dest_cds)
        all_work_days: list[date] = []
        seen: set[date] = set()
        for dest in dest_cds:
            for d in workdays_cache.get(dest, []):
                if first <= d <= last and d not in seen:
                    seen.add(d)
                    all_work_days.append(d)
        all_work_days.sort()

        distributed = _distribute_forecast(all_work_days, forecast_total)
        daily = [
            {
                "date": d.isoformat(),
                "forecast_units": qty,
                "order_units": 0,
                "weekday": WEEKDAY_JA[d.weekday()],
            }
            for d, qty in distributed
        ]
        results.append(
            {
                "year": ty,
                "month": tm,
                "source": source,
                "daily": daily,
                "monthly_total": {"forecast": forecast_total, "order": 0},
            }
        )
    return results
