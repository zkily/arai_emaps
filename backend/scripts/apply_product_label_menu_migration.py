"""Apply migration 85 for product label menu (idempotent)."""
from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(ROOT))

from scripts.bootstrap_full_database import load_db_settings  # noqa: E402


def _run_sql_file(cur, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if not stmt or stmt.startswith("--"):
            continue
        cur.execute(stmt)


def main() -> int:
    host, port, user, password, db_name = load_db_settings(None)
    conn = mysql.connector.connect(
        host=host, port=port, user=user, password=password, database=db_name
    )
    cur = conn.cursor()
    try:
        for name in ("85_product_label_menu.sql", "86_product_label_menu_parent.sql"):
            sql_path = BACKEND_ROOT / "database/migrations" / name
            if sql_path.exists():
                _run_sql_file(cur, sql_path)
        conn.commit()
        cur.execute(
            "SELECT c.code, c.name, p.code AS parent_code "
            "FROM menus c LEFT JOIN menus p ON p.id = c.parent_id "
            "WHERE c.code IN ('MASTER_LABEL', 'MASTER_PRODUCT_LABEL_CONFIG')"
        )
        for row in cur.fetchall():
            print(row)
        return 0
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
