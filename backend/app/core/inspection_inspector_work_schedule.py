"""検査員別所定稼働時間 — 稼働率分析用の解決ロジック"""
from __future__ import annotations

from datetime import date, time
from typing import Optional, Set

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master.models import InspectionInspectorWorkSchedule

DEFAULT_INSPECTION_STANDARD_HOURS = 7.6
DEFAULT_INSPECTION_STANDARD_SEC = int(DEFAULT_INSPECTION_STANDARD_HOURS * 3600)

WEEKDAY_LABELS = {
    0: "月曜",
    1: "火曜",
    2: "水曜",
    3: "木曜",
    4: "金曜",
    5: "土曜",
    6: "日曜",
}

RULE_KIND_LABELS = {
    "date": "指定日期",
    "time": "指定时间",
}


def _time_to_hm(value: Optional[time]) -> Optional[str]:
    if value is None:
        return None
    return value.strftime("%H:%M")


def _hours_from_time_range(start: Optional[time], end: Optional[time]) -> Optional[float]:
    if start is None or end is None:
        return None
    start_mins = start.hour * 60 + start.minute
    end_mins = end.hour * 60 + end.minute
    if end_mins <= start_mins:
        end_mins += 24 * 60
    return round((end_mins - start_mins) / 60, 2)


def resolve_scheduled_hours(
    *,
    scheduled_hours: Optional[float],
    work_start_time: Optional[time],
    work_end_time: Optional[time],
) -> float:
    from_range = _hours_from_time_range(work_start_time, work_end_time)
    if from_range is not None and from_range > 0:
        return from_range
    if scheduled_hours is not None and scheduled_hours > 0:
        return float(scheduled_hours)
    return DEFAULT_INSPECTION_STANDARD_HOURS


class InspectorWorkScheduleIndex:
    """検査員×日付/曜日 → 所定時間（時間）のインメモリ索引。"""

    def __init__(self) -> None:
        self._by_date: dict[tuple[int, str], float] = {}
        self._by_weekday: dict[tuple[int, int], float] = {}

    def resolve_hours(self, user_id: Optional[int], d: date) -> float:
        if user_id is None:
            return DEFAULT_INSPECTION_STANDARD_HOURS
        iso = d.isoformat()
        if (user_id, iso) in self._by_date:
            return self._by_date[(user_id, iso)]
        if (user_id, d.weekday()) in self._by_weekday:
            return self._by_weekday[(user_id, d.weekday())]
        return DEFAULT_INSPECTION_STANDARD_HOURS

    def resolve_sec(self, user_id: Optional[int], d: date) -> int:
        return int(round(self.resolve_hours(user_id, d) * 3600))


def _hours_from_row(row: InspectionInspectorWorkSchedule) -> float:
    return resolve_scheduled_hours(
        scheduled_hours=float(row.scheduled_hours) if row.scheduled_hours is not None else None,
        work_start_time=row.work_start_time,
        work_end_time=row.work_end_time,
    )


async def load_inspector_work_schedule_index(
    db: AsyncSession,
    *,
    start_d: date,
    end_d: date,
    inspector_user_ids: Set[int],
) -> InspectorWorkScheduleIndex:
    index = InspectorWorkScheduleIndex()
    if not inspector_user_ids:
        return index

    try:
        q = select(InspectionInspectorWorkSchedule).where(
            InspectionInspectorWorkSchedule.inspector_user_id.in_(list(inspector_user_ids)),
            or_(
                InspectionInspectorWorkSchedule.schedule_date.between(start_d, end_d),
                InspectionInspectorWorkSchedule.schedule_date.is_(None),
            ),
        )
        res = await db.execute(q)
        for row in res.scalars().all():
            uid = int(row.inspector_user_id)
            hours = _hours_from_row(row)
            if row.schedule_date is not None:
                index._by_date[(uid, row.schedule_date.isoformat())] = hours
            elif row.weekday is not None:
                index._by_weekday[(uid, int(row.weekday))] = hours
    except Exception:
        # 未迁移 inspection_inspector_work_schedule 等场景下回退默认 7.6h
        return InspectorWorkScheduleIndex()
    return index


def schedule_row_to_dict(row: InspectionInspectorWorkSchedule, *, inspector_name: Optional[str] = None) -> dict:
    sched_date = row.schedule_date.isoformat() if row.schedule_date else None
    wd = int(row.weekday) if row.weekday is not None else None
    rule_kind = "date" if sched_date else "time"
    start_hm = _time_to_hm(row.work_start_time)
    end_hm = _time_to_hm(row.work_end_time)
    hours = _hours_from_row(row)
    time_range_label = f"{start_hm}～{end_hm}" if start_hm and end_hm else None
    target_label = sched_date if sched_date else (WEEKDAY_LABELS.get(wd) if wd is not None else None)
    return {
        "id": row.id,
        "inspector_user_id": row.inspector_user_id,
        "inspector_name": inspector_name,
        "rule_kind": rule_kind,
        "rule_kind_label": RULE_KIND_LABELS.get(rule_kind, rule_kind),
        "schedule_date": sched_date,
        "weekday": wd,
        "weekday_label": WEEKDAY_LABELS.get(wd) if wd is not None else None,
        "target_label": target_label,
        "work_start_time": start_hm,
        "work_end_time": end_hm,
        "time_range_label": time_range_label,
        "scheduled_hours": hours,
        "note": row.note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
