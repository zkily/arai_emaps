"""Apply migration 73 for plating_production_indicator (idempotent)."""
from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(ROOT))

from scripts.bootstrap_full_database import load_db_settings  # noqa: E402


def main() -> int:
    host, port, user, password, db_name = load_db_settings(None)
    sql_path = BACKEND_ROOT / "database/migrations/73_plating_production_indicator.sql"
    sql = sql_path.read_text(encoding="utf-8")
    conn = mysql.connector.connect(
        host=host, port=port, user=user, password=password, database=db_name
    )
    cur = conn.cursor()
    try:
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if not stmt or stmt.startswith("--"):
                continue
            cur.execute(stmt)
        conn.commit()
        cur.execute("SHOW TABLES LIKE 'plating_production_indicator'")
        print("table exists:", cur.fetchone())
        return 0
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
