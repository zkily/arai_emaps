"""line_capacity_time_slots の slot_type（技術使用・保全）が稼働合算から除外されること。"""
from datetime import time
from types import SimpleNamespace

from app.modules.aps.engine import productive_hours_from_slot_rows, productive_minute_intervals_from_slots


def _slot(start: str, end: str, *, slot_type: str | None = "work", is_rest: bool = False, sort_order: int = 0):
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return SimpleNamespace(
        start_time=time(sh, sm),
        end_time=time(eh, em),
        sort_order=sort_order,
        slot_type=slot_type,
        is_rest=is_rest,
    )


def test_tech_slot_subtracts_from_work_like_rest():
    slots = [
        _slot("08:00", "17:00", slot_type="work", sort_order=0),
        _slot("11:00", "17:00", slot_type="tech", sort_order=1),
    ]
    segs = productive_minute_intervals_from_slots(slots)
    assert segs == [(8 * 60, 11 * 60)]
    assert abs(productive_hours_from_slot_rows(slots) - 3.0) < 1e-6


def test_maintenance_and_legacy_is_rest():
    slots = [
        _slot("08:00", "12:00", slot_type="work", sort_order=0),
        _slot("13:00", "17:00", slot_type="work", sort_order=1),
        _slot("10:00", "10:10", slot_type="rest", sort_order=2),
        _slot("15:00", "16:00", slot_type="maintenance", sort_order=3),
        # 移行直後の旧行: is_rest=1 / slot_type 既定 work → rest 扱い
        _slot("13:30", "13:40", slot_type="work", is_rest=True, sort_order=4),
    ]
    hours = productive_hours_from_slot_rows(slots)
    # 4h + 4h - 10min - 60min - 10min = 7h20m
    assert abs(hours - (8 - 10 / 60 - 1 - 10 / 60)) < 1e-6


def test_standalone_tech_row_does_not_add_capacity():
    slots = [
        _slot("09:00", "15:00", slot_type="tech", sort_order=0),
    ]
    assert productive_hours_from_slot_rows(slots) == 0.0
