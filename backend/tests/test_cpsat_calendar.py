from datetime import date, datetime, time
from types import SimpleNamespace

from app.modules.cpsat.calendar import (
    invert_work_windows,
    merge_intervals,
    work_windows_for_machine_day,
)


def test_invert_work_windows_lunch_and_night():
    windows = [(28800, 43200), (46800, 61200)]
    forbidden = invert_work_windows(windows, 86400)
    assert forbidden == [(0, 28800), (43200, 46800), (61200, 86400)]


def test_merge_overlaps():
    assert merge_intervals([(0, 10), (8, 20), (30, 40)]) == [(0, 20), (30, 40)]


def test_weekend_has_no_work_window():
    machine = SimpleNamespace(available_from=None, available_to=None, default_work_hours=None)
    origin = datetime(2026, 9, 5, 0, 0, 0)
    windows = work_windows_for_machine_day(
        origin=origin,
        d=date(2026, 9, 5),
        machine=machine,
        company_scheduled=set(),
        company_off=set(),
        slots=None,
        available_hours=None,
        calendar_configured=False,
    )
    assert windows == []


def test_weekday_default_shift():
    machine = SimpleNamespace(available_from=None, available_to=None, default_work_hours=None)
    origin = datetime(2026, 9, 7, 0, 0, 0)
    windows = work_windows_for_machine_day(
        origin=origin,
        d=date(2026, 9, 7),
        machine=machine,
        company_scheduled=set(),
        company_off=set(),
        slots=None,
        available_hours=None,
        calendar_configured=False,
    )
    assert windows == [(8 * 3600, 12 * 3600), (13 * 3600, 17 * 3600)]


def test_company_off_overrides_default():
    machine = SimpleNamespace(available_from=None, available_to=None, default_work_hours=None)
    origin = datetime(2026, 9, 7, 0, 0, 0)
    windows = work_windows_for_machine_day(
        origin=origin,
        d=date(2026, 9, 7),
        machine=machine,
        company_scheduled=set(),
        company_off={"2026-09-07"},
        slots=None,
        available_hours=None,
        calendar_configured=False,
    )
    assert windows == []


def test_available_from_to_window():
    machine = SimpleNamespace(
        available_from=time(9, 0), available_to=time(18, 0), default_work_hours=None
    )
    origin = datetime(2026, 9, 7, 0, 0, 0)
    windows = work_windows_for_machine_day(
        origin=origin,
        d=date(2026, 9, 7),
        machine=machine,
        company_scheduled=set(),
        company_off=set(),
        slots=None,
        available_hours=None,
        calendar_configured=False,
    )
    assert windows == [(9 * 3600, 18 * 3600)]
