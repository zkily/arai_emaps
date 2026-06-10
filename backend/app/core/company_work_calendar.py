"""会社共通稼働カレンダー — 通常稼働日判定（各モジュール共通）"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.master.models import CompanyWorkCalendar

DAY_TYPE_LABELS = {
    "workday": "平日",
    "weekend": "土日",
    "national_holiday": "祝日",
    "company_holiday": "会社休",
    "paid_leave": "有給",
    "extra_workday": "臨時出勤",
}

VALID_DAY_TYPES = frozenset(DAY_TYPE_LABELS.keys())


def default_is_scheduled_for_day_type(day_type: str, d: date) -> bool:
    if day_type == "extra_workday":
        return True
    if day_type in ("national_holiday", "company_holiday", "paid_leave", "weekend"):
        return False
    if day_type == "workday":
        return True
    return d.weekday() < 5


def infer_day_type(d: date, is_scheduled: bool) -> str:
    if is_scheduled and d.weekday() >= 5:
        return "extra_workday"
    if not is_scheduled and d.weekday() >= 5:
        return "weekend"
    if not is_scheduled:
        return "company_holiday"
    return "workday"


def iter_dates_inclusive(start_d: date, end_d: date) -> Iterable[date]:
    cur = start_d
    while cur <= end_d:
        yield cur
        cur += timedelta(days=1)


def is_scheduled_workday(
    d: date,
    *,
    company_scheduled: Set[str],
    company_off: Set[str],
    extra_workdays: Set[str],
    extra_holidays: Set[str],
) -> bool:
    """通常稼働日判定。手動 override > 会社カレンダー > デフォルト（月〜金）。"""
    iso = d.isoformat()
    if iso in extra_workdays:
        return True
    if iso in extra_holidays:
        return False
    if iso in company_off:
        return False
    if iso in company_scheduled:
        return True
    return d.weekday() < 5


def count_scheduled_workdays(
    start_d: date,
    end_d: date,
    *,
    company_scheduled: Set[str],
    company_off: Set[str],
    extra_workdays: Set[str],
    extra_holidays: Set[str],
) -> int:
    return sum(
        1
        for d in iter_dates_inclusive(start_d, end_d)
        if is_scheduled_workday(
            d,
            company_scheduled=company_scheduled,
            company_off=company_off,
            extra_workdays=extra_workdays,
            extra_holidays=extra_holidays,
        )
    )


def split_calendar_rows(rows: Iterable[CompanyWorkCalendar]) -> Tuple[Set[str], Set[str]]:
    scheduled: Set[str] = set()
    off: Set[str] = set()
    for row in rows:
        iso = row.calendar_date.isoformat()
        if row.is_scheduled:
            scheduled.add(iso)
        else:
            off.add(iso)
    return scheduled, off


async def load_company_calendar_sets(
    db: AsyncSession,
    start_d: date,
    end_d: date,
) -> Tuple[Set[str], Set[str]]:
    q = (
        select(CompanyWorkCalendar)
        .where(
            CompanyWorkCalendar.calendar_date >= start_d,
            CompanyWorkCalendar.calendar_date <= end_d,
        )
        .order_by(CompanyWorkCalendar.calendar_date)
    )
    res = await db.execute(q)
    return split_calendar_rows(res.scalars().all())


def calendar_row_to_dict(row: CompanyWorkCalendar) -> dict:
    return {
        "id": row.id,
        "calendar_date": row.calendar_date.isoformat() if row.calendar_date else None,
        "day_type": row.day_type,
        "day_type_label": DAY_TYPE_LABELS.get(row.day_type or "", row.day_type),
        "is_scheduled": bool(row.is_scheduled),
        "name": row.name,
        "note": row.note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def parse_date_csv(raw: Optional[str]) -> Set[str]:
    if not raw or not str(raw).strip():
        return set()
    out: Set[str] = set()
    for part in str(raw).split(","):
        s = part.strip()
        if s:
            out.add(s[:10])
    return out
