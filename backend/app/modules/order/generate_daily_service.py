"""
日受注リスト生成サービス
月別受注（量産品）から日別受注を生成。工作日按納入先の休日・臨時出勤で計算。
"""
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Set
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.erp import models as erp_models
from app.modules.master.models import (
    Product,
    Destination,
    DestinationHoliday,
    DestinationWorkday,
)

WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def _last_day_of_month(y: int, m: int) -> date:
    if m == 12:
        return date(y, 12, 31)
    return date(y, m + 1, 1) - timedelta(days=1)


def _is_weekend(d: date) -> bool:
    # Monday=0, Sunday=6 -> Saturday=5, Sunday=6
    return d.weekday() >= 5


async def build_working_days_cache(
    db: AsyncSession,
    year: int,
    month: int,
    destination_cds: List[str],
) -> Dict[str, List[date]]:
    """按納入先计算该年月的営業日列表（排除周末与休日，包含臨時出勤日）。"""
    first = date(year, month, 1)
    last = _last_day_of_month(year, month)
    all_days = [first + timedelta(days=i) for i in range((last - first).days + 1)]

    # 休日
    holidays_q = select(DestinationHoliday.destination_cd, DestinationHoliday.holiday_date).where(
        and_(
            DestinationHoliday.destination_cd.in_(destination_cds),
            DestinationHoliday.holiday_date >= first,
            DestinationHoliday.holiday_date <= last,
        )
    )
    hol_result = await db.execute(holidays_q)
    hol_set: Dict[str, Set[date]] = {}
    for row in hol_result.all():
        hol_set.setdefault(row.destination_cd, set()).add(row.holiday_date)

    # 臨時出勤日
    workdays_q = select(DestinationWorkday.destination_cd, DestinationWorkday.work_date).where(
        and_(
            DestinationWorkday.destination_cd.in_(destination_cds),
            DestinationWorkday.work_date >= first,
            DestinationWorkday.work_date <= last,
        )
    )
    wd_result = await db.execute(workdays_q)
    wd_set: Dict[str, Set[date]] = {}
    for row in wd_result.all():
        wd_set.setdefault(row.destination_cd, set()).add(row.work_date)

    cache: Dict[str, List[date]] = {}
    for dest_cd in destination_cds:
        h = hol_set.get(dest_cd, set())
        w = wd_set.get(dest_cd, set())
        work_days = [
            d for d in all_days
            if (not _is_weekend(d) and d not in h) or d in w
        ]
        work_days.sort()
        cache[dest_cd] = work_days
    return cache


async def run_generate_daily(
    db: AsyncSession,
    year: int,
    month: int,
    destination_cd: Optional[str] = None,
) -> dict:
    """
    生成日受注：仅处理 product_type='量産品' 的月订单。
    返回 { success, insertedCount, updatedCount, total }。
    """
    om = erp_models.OrderMonthly
    od = erp_models.OrderDaily
    query = select(om).where(
        and_(
            om.year == year,
            om.month == month,
            om.product_type == "量産品",
        )
    )
    if destination_cd:
        query = query.where(om.destination_cd == destination_cd)
    query = query.order_by(om.destination_cd, om.product_cd)
    result = await db.execute(query)
    monthly_rows = result.scalars().all()
    if not monthly_rows:
        return {"success": False, "detail": "対象の月受注が見つかりません", "insertedCount": 0, "updatedCount": 0, "total": 0}

    dest_cds = list({r.destination_cd for r in monthly_rows})
    workdays_cache = await build_working_days_cache(db, year, month, dest_cds)

    # 製品 unit_per_box（products テーブル）
    product_cds = list({r.product_cd for r in monthly_rows})
    pq = select(Product.product_cd, Product.unit_per_box).where(Product.product_cd.in_(product_cds))
    pr = await db.execute(pq)
    unit_per_box_map = {row.product_cd: (row.unit_per_box or 0) for row in pr.all()}

    # 納入先 delivery_lead_time（destinations テーブル）
    dq = select(Destination.destination_cd, Destination.delivery_lead_time).where(
        Destination.destination_cd.in_(dest_cds)
    )
    dr = await db.execute(dq)
    lead_time_map = {row.destination_cd: (row.delivery_lead_time or 0) for row in dr.all()}

    inserted = 0
    updated = 0
    first = date(year, month, 1)
    last = _last_day_of_month(year, month)

    for row in monthly_rows:
        order_id = row.order_id
        dest_cd = row.destination_cd
        work_days = workdays_cache.get(dest_cd) or []
        if not work_days:
            continue
        unit_per_box = unit_per_box_map.get(row.product_cd, 0) or 0
        lead_time = lead_time_map.get(dest_cd, 0) or 0
        forecast = row.forecast_units or 0

        # 既存日受注（该月订单 + 该年月）
        existing_q = select(od).where(
            and_(
                od.monthly_order_id == order_id,
                od.date >= first,
                od.date <= last,
            )
        )
        ex_result = await db.execute(existing_q)
        existing_list = {r.date: r for r in ex_result.scalars().all()}

        # 分配策略：月内示 < 1100 → 第3工作日集中；否则工作日平均
        if forecast < 1100:
            per_day = [0] * len(work_days)
            if len(work_days) >= 3 and forecast > 0:
                per_day[2] = forecast
            else:
                if work_days and forecast > 0:
                    per_day[0] = forecast
        else:
            base, rem = divmod(forecast, len(work_days))
            per_day = [base] * len(work_days)
            for i in range(rem):
                per_day[-(1 + i)] += 1

        for i, d in enumerate(work_days):
            qty = per_day[i] if i < len(per_day) else 0
            # delivery_date: 工作日 + lead_time 営業日（此处简化为自然日）
            delivery = d + timedelta(days=lead_time) if lead_time else d
            weekday_ja = WEEKDAY_JA[d.weekday()]
            existing = existing_list.get(d)
            if existing:
                existing.forecast_units = qty
                existing.unit_per_box = unit_per_box
                existing.delivery_date = delivery
                existing.weekday = weekday_ja
                updated += 1
            else:
                new_daily = erp_models.OrderDaily(
                    monthly_order_id=order_id,
                    destination_cd=dest_cd,
                    destination_name=row.destination_name,
                    date=d,
                    weekday=weekday_ja,
                    product_cd=row.product_cd,
                    product_name=row.product_name,
                    product_alias=row.product_alias,
                    product_type=row.product_type,
                    forecast_units=qty,
                    confirmed_units=0,
                    confirmed_boxes=0,
                    unit_per_box=unit_per_box,
                    delivery_date=delivery,
                    status="未出荷",
                )
                db.add(new_daily)
                inserted += 1

    await db.flush()

    # 更新 order_monthly 的 forecast_total_units（日订单 confirmed 合计）/ forecast_diff
    for row in monthly_rows:
        sum_q = select(func.coalesce(func.sum(od.confirmed_units), 0)).where(
            and_(
                od.monthly_order_id == row.order_id,
                od.date >= first,
                od.date <= last,
            )
        )
        sum_r = await db.execute(sum_q)
        total_confirmed = int(sum_r.scalar() or 0)
        row.forecast_total_units = total_confirmed
        # 内示差異 = 確定本数 - 内示本数
        row.forecast_diff = total_confirmed - (row.forecast_units or 0)

    return {
        "success": True,
        "insertedCount": inserted,
        "updatedCount": updated,
        "total": len(monthly_rows),
    }
