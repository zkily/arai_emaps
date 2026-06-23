"""レポート定時配信スケジューラ（daily / weekly / monthly）"""
from __future__ import annotations

import calendar
from datetime import datetime, time as time_of_day, timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reports.models import ReportSchedule
from app.services.full_database_backup import local_now_for_schedule
from app.services.report_delivery_service import send_report


def _schedule_time(schedule: ReportSchedule) -> time_of_day:
    t = schedule.schedule_time
    if isinstance(t, time_of_day):
        return t
    return time_of_day(8, 0)


def _is_due(schedule: ReportSchedule, now_local: datetime) -> bool:
    """当日まだ実行していない & 予定時刻を過ぎているか。"""
    sched_time = _schedule_time(schedule)
    if now_local.time() < sched_time:
        return False
    if schedule.last_run_at and schedule.last_run_at.date() >= now_local.date():
        return False

    config = schedule.schedule_config or {}
    stype = (schedule.schedule_type or "daily").lower()
    if stype == "daily":
        return True
    if stype == "weekly":
        weekday = int(config.get("weekday", 0))
        return now_local.weekday() == weekday
    if stype == "monthly":
        day = int(config.get("day", 1))
        last_day = calendar.monthrange(now_local.year, now_local.month)[1]
        return now_local.day == min(day, last_day)
    return False


def _compute_next_run_at(schedule: ReportSchedule, from_local: datetime) -> datetime | None:
    sched_time = _schedule_time(schedule)
    stype = (schedule.schedule_type or "daily").lower()
    config = schedule.schedule_config or {}
    base = from_local.replace(hour=sched_time.hour, minute=sched_time.minute, second=0, microsecond=0)

    if stype == "daily":
        nxt = base if base > from_local else base + timedelta(days=1)
        return nxt
    if stype == "weekly":
        weekday = int(config.get("weekday", 0))
        days_ahead = (weekday - from_local.weekday()) % 7
        candidate = base + timedelta(days=days_ahead)
        if candidate <= from_local:
            candidate += timedelta(days=7)
        return candidate
    if stype == "monthly":
        day = int(config.get("day", 1))
        year, month = from_local.year, from_local.month
        for _ in range(2):
            last_day = calendar.monthrange(year, month)[1]
            candidate = base.replace(year=year, month=month, day=min(day, last_day))
            if candidate > from_local:
                return candidate
            month = 1 if month == 12 else month + 1
            year = year + 1 if month == 1 else year
    return None


async def run_due_report_schedules_once(db: AsyncSession) -> dict:
    """有効なスケジュールを走査し、実行時刻を過ぎたものを 1 回ずつ配信する。"""
    result = await db.execute(
        select(ReportSchedule).where(ReportSchedule.is_active.is_(True))
    )
    schedules = result.scalars().all()
    now_local = local_now_for_schedule()

    ran: list[dict] = []
    for schedule in schedules:
        if not _is_due(schedule, now_local):
            continue
        try:
            send_result = await send_report(
                db,
                report_code=schedule.report_code,
                parameters=schedule.parameters or {},
                fmt=schedule.format,
                trigger="scheduled",
                current_user=None,
                run_date=now_local.date(),
            )
            schedule.last_run_at = now_local
            schedule.next_run_at = _compute_next_run_at(schedule, now_local)
            await db.commit()
            ran.append({"report_code": schedule.report_code, "status": send_result.get("status")})
            logger.info(
                "📨 レポート定時配信: code={} status={}",
                schedule.report_code,
                send_result.get("status"),
            )
        except Exception as exc:
            await db.rollback()
            logger.warning("レポート定時配信でエラー: code={} err={}", schedule.report_code, exc)
            ran.append({"report_code": schedule.report_code, "status": "error", "error": str(exc)})

    return {"checked": len(schedules), "ran": ran}
