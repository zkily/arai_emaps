"""Apply migration 128_rename_label_menus_display.sql (idempotent)."""
from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402

MIGRATION_FILE = BACKEND_ROOT / "database" / "migrations" / "128_rename_label_menus_display.sql"


def main() -> None:
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
            print(f"OK: {' '.join(stmt.split())[:90]}")
        conn.commit()
        print("menu names updated: 表示発行 / 各種表示印刷")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
