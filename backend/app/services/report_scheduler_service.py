"""レポート定時配信スケジューラ（daily / weekly / monthly）"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, replace
from datetime import datetime, time as time_of_day, timedelta
from typing import Any

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst_naive
from app.modules.reports.models import ReportSchedule
from app.services.report_delivery_service import send_report


@dataclass(frozen=True)
class ScheduleSnapshot:
    """ORM を同期関数に渡さないためのスナップショット（MissingGreenlet 回避）。"""

    id: int
    report_code: str
    schedule_type: str
    schedule_time: Any
    schedule_config: dict[str, Any] | None
    parameters: dict[str, Any] | None
    format: str | None
    last_run_at: datetime | None
    next_run_at: datetime | None


def _snapshot_schedule(schedule: ReportSchedule) -> ScheduleSnapshot:
    return ScheduleSnapshot(
        id=schedule.id,
        report_code=schedule.report_code,
        schedule_type=schedule.schedule_type or "daily",
        schedule_time=schedule.schedule_time,
        schedule_config=dict(schedule.schedule_config) if schedule.schedule_config else None,
        parameters=dict(schedule.parameters) if schedule.parameters else None,
        format=schedule.format,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
    )


def _schedule_time(snapshot: ScheduleSnapshot) -> time_of_day:
    """MySQL TIME 列が timedelta で返る場合にも対応。"""
    t = snapshot.schedule_time
    if isinstance(t, time_of_day):
        return t
    if isinstance(t, timedelta):
        total = int(t.total_seconds()) % (24 * 3600)
        return (datetime.min + timedelta(seconds=total)).time()
    if isinstance(t, str):
        parts = t.strip().split(":")
        if len(parts) >= 2:
            h, m = int(parts[0]), int(parts[1])
            s = int(parts[2]) if len(parts) > 2 else 0
            return time_of_day(h, m, s)
    return time_of_day(8, 0)


def _matches_schedule_calendar(snapshot: ScheduleSnapshot, now_local: datetime) -> bool:
    config = snapshot.schedule_config or {}
    stype = snapshot.schedule_type.lower()
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


def _is_due(snapshot: ScheduleSnapshot, now_local: datetime) -> bool:
    """実行予定時刻（JST）を過ぎており、当該回は未実行か。"""
    if snapshot.next_run_at and now_local < snapshot.next_run_at:
        return False

    sched_time = _schedule_time(snapshot)

    if snapshot.next_run_at and now_local >= snapshot.next_run_at:
        if snapshot.last_run_at and snapshot.last_run_at >= snapshot.next_run_at:
            return False
        return _matches_schedule_calendar(snapshot, now_local)

    # next_run_at 未設定（旧データ）のフォールバック
    if now_local.time() < sched_time:
        return False
    if snapshot.last_run_at and snapshot.last_run_at.date() >= now_local.date():
        return False
    return _matches_schedule_calendar(snapshot, now_local)


def compute_next_run_at(snapshot: ScheduleSnapshot, from_local: datetime) -> datetime | None:
    """次回実行予定（JST 壁時計）を算出。"""
    sched_time = _schedule_time(snapshot)
    stype = snapshot.schedule_type.lower()
    config = snapshot.schedule_config or {}
    base = from_local.replace(hour=sched_time.hour, minute=sched_time.minute, second=0, microsecond=0)

    if stype == "daily":
        return base if base > from_local else base + timedelta(days=1)
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


async def _update_schedule_run_state(
    db: AsyncSession,
    *,
    schedule_id: int,
    last_run_at: datetime | None = None,
    next_run_at: datetime | None = None,
) -> None:
    values: dict[str, datetime] = {}
    if last_run_at is not None:
        values["last_run_at"] = last_run_at
    if next_run_at is not None:
        values["next_run_at"] = next_run_at
    if values:
        await db.execute(update(ReportSchedule).where(ReportSchedule.id == schedule_id).values(**values))


async def refresh_schedule_next_run_at(db: AsyncSession, schedule: ReportSchedule) -> None:
    """スケジュール保存時に次回実行予定を JST で再計算。"""
    snapshot = _snapshot_schedule(schedule)
    schedule.next_run_at = compute_next_run_at(snapshot, now_jst_naive())


async def run_due_report_schedules_once(db: AsyncSession) -> dict:
    """有効なスケジュールを走査し、実行時刻を過ぎたものを 1 回ずつ配信する。"""
    result = await db.execute(
        select(ReportSchedule).where(ReportSchedule.is_active.is_(True))
    )
    schedules = result.scalars().all()
    now_local = now_jst_naive()

    ran: list[dict] = []
    for schedule in schedules:
        snapshot = _snapshot_schedule(schedule)

        if snapshot.next_run_at is None:
            next_run = compute_next_run_at(snapshot, now_local)
            await _update_schedule_run_state(db, schedule_id=snapshot.id, next_run_at=next_run)
            await db.commit()
            snapshot = replace(snapshot, next_run_at=next_run)

        if not _is_due(snapshot, now_local):
            continue

        report_code = snapshot.report_code
        try:
            send_result = await send_report(
                db,
                report_code=report_code,
                parameters=snapshot.parameters or {},
                fmt=snapshot.format,
                trigger="scheduled",
                current_user=None,
                run_date=now_local.date(),
            )
            next_run = compute_next_run_at(snapshot, now_local)
            await _update_schedule_run_state(
                db,
                schedule_id=snapshot.id,
                last_run_at=now_local,
                next_run_at=next_run,
            )
            await db.commit()
            ran.append({"report_code": report_code, "status": send_result.get("status")})
            logger.info(
                "📨 レポート定時配信: code={} status={}",
                report_code,
                send_result.get("status"),
            )
        except Exception as exc:
            await db.rollback()
            logger.warning("レポート定時配信でエラー: code={} err={}", report_code, exc)
            ran.append({"report_code": report_code, "status": "error", "error": str(exc)})

    return {"checked": len(schedules), "ran": ran}
