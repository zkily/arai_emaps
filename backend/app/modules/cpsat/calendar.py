"""設備の稼働日・時間帯を CP-SAT の禁止区間へ変換する。"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.company_work_calendar import (
    is_scheduled_workday,
    iter_dates_inclusive,
    load_company_calendar_sets,
)
from app.modules.aps.engine import productive_minute_intervals_from_slots
from app.modules.aps.models import LineCapacity, LineCapacityTimeSlot
from app.modules.master.models import Machine, MachineWorkTimeConfig

DEFAULT_DAY_START = time(8, 0)
CAPACITY_DAY_START = time(6, 0)
DEFAULT_WINDOWS = ((time(8, 0), time(12, 0)), (time(13, 0), time(17, 0)))
OVERTIME_WINDOWS = (
    ("time_slot_6_8", time(6, 0), time(8, 0)),
    ("time_slot_17_19", time(17, 0), time(19, 0)),
    ("time_slot_19_21", time(19, 0), time(21, 0)),
)
_FALLBACK_MACHINE = SimpleNamespace(
    id=0,
    available_from=None,
    available_to=None,
    default_work_hours=None,
)


def merge_intervals(ivs: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    items = sorted((int(s), int(e)) for s, e in ivs if e > s)
    if not items:
        return []
    out: list[tuple[int, int]] = [items[0]]
    for s, e in items[1:]:
        ps, pe = out[-1]
        if s <= pe:
            out[-1] = (ps, max(pe, e))
        else:
            out.append((s, e))
    return out


def invert_work_windows(
    windows: Iterable[tuple[int, int]], horizon_sec: int
) -> list[tuple[int, int]]:
    """稼働窓の補集合（非稼働区間）。"""
    horizon = max(int(horizon_sec), 0)
    if horizon <= 0:
        return []
    cursor = 0
    forbidden: list[tuple[int, int]] = []
    for s, e in merge_intervals((max(0, a), min(horizon, b)) for a, b in windows):
        if s > cursor:
            forbidden.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < horizon:
        forbidden.append((cursor, horizon))
    return forbidden


def _dt_on(d: date, t: time) -> datetime:
    return datetime.combine(d, t)


def _wall_sec(origin: datetime, dt: datetime) -> int:
    return int((dt - origin).total_seconds())


def _window_on_day(origin: datetime, d: date, start_t: time, end_t: time) -> list[tuple[int, int]]:
    start = _dt_on(d, start_t)
    end = _dt_on(d, end_t)
    if end <= start:
        end = end + timedelta(days=1)
    s = max(0, _wall_sec(origin, start))
    e = _wall_sec(origin, end)
    return [(s, e)] if e > s else []


def _windows_from_minutes(
    origin: datetime, d: date, segs: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    midnight = _dt_on(d, time(0, 0))
    for sm, em in segs:
        if em <= sm:
            continue
        s = _wall_sec(origin, midnight + timedelta(minutes=sm))
        e = _wall_sec(origin, midnight + timedelta(minutes=em))
        if e > s:
            out.append((max(0, s), e))
    return out


def _hours_window(origin: datetime, d: date, start_t: time, hours: float) -> list[tuple[int, int]]:
    if hours <= 0:
        return []
    start = _dt_on(d, start_t)
    end = start + timedelta(hours=float(hours))
    s = max(0, _wall_sec(origin, start))
    e = _wall_sec(origin, end)
    return [(s, e)] if e > s else []


def _overtime_windows(origin: datetime, d: date, cfg) -> list[tuple[int, int]]:
    if cfg is None:
        return []
    out: list[tuple[int, int]] = []
    for attr, a, b in OVERTIME_WINDOWS:
        if getattr(cfg, attr, 0):
            out.extend(_window_on_day(origin, d, a, b))
    return out


def _fallback_windows(
    origin: datetime, d: date, machine, overtime_cfg=None
) -> list[tuple[int, int]]:
    af = getattr(machine, "available_from", None)
    at = getattr(machine, "available_to", None)
    if af is not None and at is not None and (af != at):
        return _window_on_day(origin, d, af, at) + _overtime_windows(origin, d, overtime_cfg)
    hours = float(getattr(machine, "default_work_hours", 0) or 0)
    if hours > 0:
        start = af or DEFAULT_DAY_START
        return _hours_window(origin, d, start, hours) + _overtime_windows(origin, d, overtime_cfg)
    out: list[tuple[int, int]] = []
    for a, b in DEFAULT_WINDOWS:
        out.extend(_window_on_day(origin, d, a, b))
    out.extend(_overtime_windows(origin, d, overtime_cfg))
    return out


def work_windows_for_machine_day(
    *,
    origin: datetime,
    d: date,
    machine,
    company_scheduled: set[str],
    company_off: set[str],
    slots: list[LineCapacityTimeSlot] | None,
    available_hours: Optional[float],
    calendar_configured: bool,
    overtime_cfg=None,
) -> list[tuple[int, int]]:
    if not is_scheduled_workday(
        d,
        company_scheduled=company_scheduled,
        company_off=company_off,
        extra_workdays=set(),
        extra_holidays=set(),
    ):
        return []
    if slots:
        segs = productive_minute_intervals_from_slots(slots)
        return _windows_from_minutes(origin, d, segs)
    if available_hours is not None:
        if available_hours <= 0:
            return []
        start = getattr(machine, "available_from", None) or CAPACITY_DAY_START
        return _hours_window(origin, d, start, float(available_hours))
    if calendar_configured:
        return []
    return _fallback_windows(origin, d, machine, overtime_cfg)


async def load_forbidden_by_machine(
    db: AsyncSession,
    *,
    origin: datetime,
    horizon_sec: int,
    machine_cds: Iterable[str],
) -> dict[str, list[tuple[int, int]]]:
    cds = sorted({(c or "").strip() for c in machine_cds if c and str(c).strip()})
    if not cds or horizon_sec <= 0:
        return {}
    horizon_end = origin + timedelta(seconds=int(horizon_sec))
    start_d = origin.date()
    end_d = horizon_end.date()
    company_scheduled, company_off = await load_company_calendar_sets(db, start_d, end_d)

    machines = (
        (await db.execute(select(Machine).where(Machine.machine_cd.in_(cds)))).scalars().all()
    )
    by_cd = {m.machine_cd: m for m in machines}
    line_ids = [int(m.id) for m in machines]
    overtime_rows = (
        (
            await db.execute(
                select(MachineWorkTimeConfig).where(MachineWorkTimeConfig.machine_cd.in_(cds))
            )
        )
        .scalars()
        .all()
    )
    overtime_by_cd = {r.machine_cd: r for r in overtime_rows}

    cap_map: dict[int, dict[date, float]] = defaultdict(dict)
    slots_map: dict[int, dict[date, list[LineCapacityTimeSlot]]] = defaultdict(
        lambda: defaultdict(list)
    )
    if line_ids:
        caps = (
            (
                await db.execute(
                    select(LineCapacity).where(
                        LineCapacity.line_id.in_(line_ids),
                        LineCapacity.work_date >= start_d,
                        LineCapacity.work_date <= end_d,
                    )
                )
            )
            .scalars()
            .all()
        )
        for row in caps:
            cap_map[int(row.line_id)][row.work_date] = float(row.available_hours or 0)
        slots = (
            (
                await db.execute(
                    select(LineCapacityTimeSlot)
                    .where(
                        LineCapacityTimeSlot.line_id.in_(line_ids),
                        LineCapacityTimeSlot.work_date >= start_d,
                        LineCapacityTimeSlot.work_date <= end_d,
                    )
                    .order_by(LineCapacityTimeSlot.work_date, LineCapacityTimeSlot.sort_order)
                )
            )
            .scalars()
            .all()
        )
        for row in slots:
            slots_map[int(row.line_id)][row.work_date].append(row)

    out: dict[str, list[tuple[int, int]]] = {}
    for cd in cds:
        machine = by_cd.get(cd) or _FALLBACK_MACHINE
        lid = int(getattr(machine, "id", 0) or 0)
        cal = cap_map.get(lid, {})
        slots_by_date = slots_map.get(lid, {})
        configured = bool(cal) or any(slots_by_date.values())
        work: list[tuple[int, int]] = []
        for d in iter_dates_inclusive(start_d, end_d):
            hours = cal.get(d)
            work.extend(
                work_windows_for_machine_day(
                    origin=origin,
                    d=d,
                    machine=machine,
                    company_scheduled=company_scheduled,
                    company_off=company_off,
                    slots=slots_by_date.get(d),
                    available_hours=hours,
                    calendar_configured=configured,
                    overtime_cfg=overtime_by_cd.get(cd),
                )
            )
        out[cd] = invert_work_windows(work, horizon_sec)
    return out
