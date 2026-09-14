"""Apply migration 126_file_watcher_manager_menu.sql (idempotent)."""
from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402

MIGRATION_FILE = BACKEND_ROOT / "database" / "migrations" / "126_file_watcher_manager_menu.sql"


def main() -> None:
    if not MIGRATION_FILE.is_file():
        raise SystemExit(f"migration file not found: {MIGRATION_FILE}")

    raw = MIGRATION_FILE.read_text(encoding="utf-8")
    sql = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("--"))
    statements = [chunk.strip() for chunk in sql.split(";") if chunk.strip()]

    conn = mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
    )
    cur = conn.cursor()
    try:
        for stmt in statements:
            cur.execute(stmt)
            preview = " ".join(stmt.split())[:90]
            print(f"OK: {preview}")
        conn.commit()
        print("menu SYSTEM_FILE_WATCHER_MANAGER applied")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
