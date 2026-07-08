"""Apply migration 80 for product_label_config (idempotent)."""
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
    sql_path = BACKEND_ROOT / "database/migrations/80_product_label_config.sql"
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
        collation_path = BACKEND_ROOT / "database/migrations/81_product_label_config_collation.sql"
        if collation_path.exists():
            collation_sql = collation_path.read_text(encoding="utf-8")
            for stmt in collation_sql.split(";"):
                stmt = stmt.strip()
                if not stmt or stmt.startswith("--"):
                    continue
                cur.execute(stmt)
            conn.commit()
        upper_lock_path = BACKEND_ROOT / "database/migrations/82_product_label_config_upper_slots_locked.sql"
        if upper_lock_path.exists():
            upper_lock_sql = upper_lock_path.read_text(encoding="utf-8")
            for stmt in upper_lock_sql.split(";"):
                stmt = stmt.strip()
                if not stmt or stmt.startswith("--"):
                    continue
                try:
                    cur.execute(stmt)
                except mysql.connector.Error as exc:
                    if exc.errno != 1060:
                        raise
            conn.commit()
        cur.execute("SHOW TABLES LIKE 'product_label_config'")
        print("table exists:", cur.fetchone())
        return 0
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
