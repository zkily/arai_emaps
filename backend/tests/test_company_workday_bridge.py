from datetime import date

from app.core.company_work_calendar import next_scheduled_workday, previous_scheduled_workday


def test_weekend_bridge_fri_mon():
    # 会社カレンダー未設定時は月〜金が稼働日
    empty: set[str] = set()
    fri = date(2026, 9, 4)  # Friday
    mon = date(2026, 9, 7)  # Monday
    assert next_scheduled_workday(
        fri,
        company_scheduled=empty,
        company_off=empty,
    ) == mon
    assert previous_scheduled_workday(
        mon,
        company_scheduled=empty,
        company_off=empty,
    ) == fri


def test_company_holiday_bridge():
    empty: set[str] = set()
    # 火曜を会社休にすると、月曜の次稼働は水曜
    mon = date(2026, 9, 7)
    tue = date(2026, 9, 8)
    wed = date(2026, 9, 9)
    assert next_scheduled_workday(
        mon,
        company_scheduled=empty,
        company_off={tue.isoformat()},
    ) == wed
    assert previous_scheduled_workday(
        wed,
        company_scheduled=empty,
        company_off={tue.isoformat()},
    ) == mon
