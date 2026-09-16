"""Reset PLAN_BASELINE_WEEKLY next_run_at to ~2 minutes from now for testing."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

import mysql.connector
from scripts.bootstrap_full_database import load_db_settings


def main() -> int:
    host, port, user, password, db_name = load_db_settings(None)
    conn = mysql.connector.connect(
        host=host, port=port, user=user, password=password, database=db_name
    )
    cur = conn.cursor()
    # JST wall clock approx: machine local is JST for this project
    slot = (datetime.now() + timedelta(minutes=2)).replace(second=0, microsecond=0)
    time_str = slot.strftime("%H:%M:%S")
    cur.execute(
        """
        UPDATE report_schedules
        SET schedule_time = %s,
            next_run_at = %s,
            last_run_at = NULL,
            updated_at = NOW()
        WHERE report_code = 'PLAN_BASELINE_WEEKLY' AND is_active = 1
        """,
        (time_str, slot),
    )
    conn.commit()
    cur.execute(
        "SELECT id, schedule_time, last_run_at, next_run_at FROM report_schedules "
        "WHERE report_code='PLAN_BASELINE_WEEKLY'"
    )
    print("updated:", cur.fetchall())
    print(f"next slot: {slot.isoformat(sep=' ', timespec='minutes')}")
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
