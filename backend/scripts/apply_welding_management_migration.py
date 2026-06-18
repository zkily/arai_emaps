"""Apply migration 55 for welding_management external sync (idempotent)."""
from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(ROOT))

from scripts.bootstrap_full_database import load_db_settings  # noqa: E402


def _try_execute(cur, stmt: str, label: str) -> None:
    try:
        cur.execute(stmt)
        print(f"OK: {label}")
    except mysql.connector.Error as exc:
        err = str(exc)
        if exc.errno in (1060, 1061, 1062) or "Duplicate column name" in err or "Duplicate key name" in err:
            print(f"SKIP (exists): {label}")
            return
        raise


def main() -> int:
    host, port, user, password, db_name = load_db_settings(None)
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        charset="utf8mb4",
    )
    cur = conn.cursor()
    try:
        _try_execute(
            cur,
            """
            ALTER TABLE welding_management
              ADD COLUMN external_sync_key varchar(64) NULL DEFAULT NULL
                COMMENT '外部Excel同期キー（内容ハッシュ・重複防止）'
                AFTER remarks
            """,
            "welding_management.external_sync_key",
        )
        _try_execute(
            cur,
            "ALTER TABLE welding_management ADD UNIQUE INDEX uk_welding_external_sync_key (external_sync_key)",
            "uk_welding_external_sync_key",
        )
        _try_execute(
            cur,
            """
            ALTER TABLE welding_management
              ADD COLUMN data_source varchar(16) NOT NULL DEFAULT 'mes'
                COMMENT '取得元: mes=溶接実績収集, excel=管理指標Excel同期, csv=一括取込'
                AFTER external_sync_key
            """,
            "welding_management.data_source",
        )
        _try_execute(
            cur,
            "ALTER TABLE welding_management ADD INDEX idx_welding_data_source (data_source)",
            "idx_welding_data_source",
        )
        _try_execute(
            cur,
            """
            ALTER TABLE welding_management
              ADD COLUMN mes_shift_sec INT NULL DEFAULT NULL COMMENT 'Excelシフト秒' AFTER mes_paused_accum_sec,
              ADD COLUMN mes_break_sec INT NULL DEFAULT NULL COMMENT 'Excel休憩秒' AFTER mes_shift_sec,
              ADD COLUMN mes_stop_sec INT NULL DEFAULT NULL COMMENT 'Excel停止等秒' AFTER mes_break_sec
            """,
            "welding_management mes_shift/break/stop sec",
        )
        conn.commit()
        print("Migration 55 complete.")
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
