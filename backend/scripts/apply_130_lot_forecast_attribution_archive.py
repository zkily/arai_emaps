"""Apply 130_lot_forecast_attribution_archive.sql (idempotent)."""
from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402


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


def _index_exists(cur, table: str, index: str) -> bool:
    cur.execute(
        """
        SELECT COUNT(1)
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME = %s
        """,
        (table, index),
    )
    return int((cur.fetchone() or (0,))[0] or 0) > 0


def main() -> None:
    conn = mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset="utf8mb4",
    )
    cur = conn.cursor()
    try:
        if not _table_exists(cur, "lot_forecast_attribution"):
            raise SystemExit("lot_forecast_attribution テーブルが存在しません")

        if not _table_exists(cur, "lot_forecast_attribution_archive"):
            cur.execute(
                "CREATE TABLE lot_forecast_attribution_archive LIKE lot_forecast_attribution"
            )
            print("created lot_forecast_attribution_archive")
        else:
            print("lot_forecast_attribution_archive already exists")

        cur.execute(
            "ALTER TABLE lot_forecast_attribution_archive "
            "COMMENT = '日内示帰属の無効版退避（lot_forecast_attribution の is_current=0 から移動）'"
        )

        if not _column_exists(cur, "lot_forecast_attribution_archive", "archived_at"):
            cur.execute(
                """
                ALTER TABLE lot_forecast_attribution_archive
                  ADD COLUMN archived_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    COMMENT 'ホットテーブルから退避した日時' AFTER computed_at,
                  ADD KEY idx_archived_at (archived_at)
                """
            )
            print("added archived_at")
        else:
            print("archived_at already exists")

        if not _index_exists(cur, "lot_forecast_attribution", "idx_lfa_is_current"):
            cur.execute(
                """
                ALTER TABLE lot_forecast_attribution
                  ADD INDEX idx_lfa_is_current (is_current),
                  ALGORITHM=INPLACE, LOCK=NONE
                """
            )
            print("added idx_lfa_is_current")
        else:
            print("idx_lfa_is_current already exists")

        conn.commit()
        print("migration 130 ok")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
