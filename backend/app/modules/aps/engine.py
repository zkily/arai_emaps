"""
APS 排産エンジン
JST 強制の産能推算ループ。schedule_details を生成し production_schedules を更新する。
"""
import math
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.aps.models import (
    ProductionLine,
    LineCapacity,
    ProductionSchedule,
    ScheduleDetail,
)


async def run_engine(
    db: AsyncSession,
    schedule_id: int,
    override_start_date: Optional[date] = None,
) -> ProductionSchedule:
    """
    指定された工単に対して排産推算を実行する。

    1. schedule_details を全削除（冪等）
    2. line_capacities から稼働時間を読み込み
    3. 日ごとに産能を計算し schedule_details を INSERT
    4. production_schedules の start_date / end_date / planned_output_qty / completion_rate を更新
    """
    ps = await db.get(ProductionSchedule, schedule_id)
    if ps is None:
        raise ValueError(f"ProductionSchedule id={schedule_id} not found")

    line = await db.get(ProductionLine, ps.line_id)
    if line is None:
        raise ValueError(f"ProductionLine id={ps.line_id} not found")

    # 既存明細の削除（冪等性）
    await db.execute(
        delete(ScheduleDetail).where(ScheduleDetail.schedule_id == schedule_id)
    )
    await db.flush()

    # 基本パラメータ
    start = override_start_date or ps.start_date or now_jst().date()
    remaining = int(ps.planned_process_qty or 0) + int(ps.prev_month_carryover or 0)
    if remaining <= 0:
        ps.start_date = start
        ps.end_date = start
        ps.planned_output_qty = 0
        ps.completion_rate = Decimal("100.00")
        ps.status = "COMPLETED"
        return ps

    daily_capacity = int(ps.daily_capacity or 0)
    if daily_capacity <= 0:
        raise ValueError("daily_capacity must be > 0")

    default_hours = float(line.default_work_hours or 0)
    if default_hours <= 0:
        default_hours = 8.0

    efficiency_pct = float(ps.efficiency or 100)
    setup_minutes = int(ps.setup_time or 0)

    # 稼働カレンダーを先読み（最大 365 日分）
    cal_end = start + timedelta(days=365)
    cal_result = await db.execute(
        select(LineCapacity)
        .where(
            LineCapacity.line_id == ps.line_id,
            LineCapacity.work_date >= start,
            LineCapacity.work_date <= cal_end,
        )
        .order_by(LineCapacity.work_date)
    )
    cal_map: dict[date, float] = {
        row.work_date: float(row.available_hours) for row in cal_result.scalars().all()
    }

    total_produced = 0
    current_date = start
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    is_first_day = True
    max_iterations = 730

    while remaining > 0 and max_iterations > 0:
        max_iterations -= 1
        avail_hours = cal_map.get(current_date, float(default_hours))

        if avail_hours <= 0:
            current_date += timedelta(days=1)
            continue

        effective_hours = avail_hours
        if is_first_day and setup_minutes > 0:
            effective_hours = max(0.0, avail_hours - setup_minutes / 60.0)
            is_first_day = False

        if effective_hours <= 0:
            current_date += timedelta(days=1)
            continue

        hourly_rate = daily_capacity / default_hours
        today_max = effective_hours * hourly_rate * (efficiency_pct / 100.0)
        today_qty = min(math.floor(today_max), remaining)

        if today_qty <= 0 and remaining > 0:
            today_qty = min(1, remaining)

        if today_qty > 0:
            db.add(ScheduleDetail(
                schedule_id=schedule_id,
                schedule_date=current_date,
                planned_qty=today_qty,
            ))
            remaining -= today_qty
            total_produced += today_qty
            if actual_start is None:
                actual_start = current_date
            actual_end = current_date

        current_date += timedelta(days=1)

    ps.start_date = actual_start or start
    ps.end_date = actual_end or start
    ps.planned_output_qty = total_produced
    total_needed = int(ps.planned_process_qty or 0) + int(ps.prev_month_carryover or 0)
    if total_needed > 0:
        ps.completion_rate = Decimal(str(round(total_produced / total_needed * 100, 2)))
    else:
        ps.completion_rate = Decimal("100.00")

    if remaining <= 0:
        ps.due_date = actual_end
    if ps.status == "PLANNING" and total_produced > 0:
        ps.status = "PLANNING"

    return ps
