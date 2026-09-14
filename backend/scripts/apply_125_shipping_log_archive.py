"""Apply 125_shipping_log_archive.sql (idempotent)."""
from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402

MIGRATION_FILE = BACKEND_ROOT / "database" / "migrations" / "125_shipping_log_archive.sql"


def _table_exists(cur, name: str) -> bool:
    cur.execute(
        """
        SELECT COUNT(1)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (name,),
    )
    return int((cur.fetchone() or (0,))[0] or 0) > 0


def _column_exists(cur, table: str, column: str) -> bool:
    cur.execute(
        """
        SELECT COUNT(1)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table, column),
    )
    return int((cur.fetchone() or (0,))[0] or 0) > 0


def main() -> None:
    if not MIGRATION_FILE.is_file():
        raise SystemExit(f"migration file not found: {MIGRATION_FILE}")

    conn = mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
    )
    cur = conn.cursor()
    try:
        if not _table_exists(cur, "shipping_log"):
            raise SystemExit("shipping_log テーブルが存在しません")

        if not _table_exists(cur, "shipping_log_archive"):
            cur.execute("CREATE TABLE shipping_log_archive LIKE shipping_log")
            print("created shipping_log_archive")
        else:
            print("shipping_log_archive already exists")

        cur.execute(
            "ALTER TABLE shipping_log_archive COMMENT = '出荷ピッキングログ退避（shipping_log から移動）'"
        )

        if not _column_exists(cur, "shipping_log_archive", "archived_at"):
            cur.execute(
                """
                ALTER TABLE shipping_log_archive
                  ADD COLUMN archived_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    COMMENT 'shipping_log から退避した日時' AFTER updated_at,
                  ADD KEY idx_archived_at (archived_at)
                """
            )
            print("added archived_at")
        else:
            print("archived_at already exists")

        conn.commit()
        print("migration ok")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
