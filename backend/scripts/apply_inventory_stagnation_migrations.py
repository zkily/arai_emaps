"""Apply migrations 53/54 for inventory stagnation notification (idempotent)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402


async def _try_execute(db, stmt: str, label: str) -> None:
    try:
        await db.execute(text(stmt))
        print(f"OK: {label}")
    except Exception as exc:
        err = str(exc)
        if "Duplicate column name" in err or "1060" in err:
            print(f"SKIP (exists): {label}")
            return
        raise


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await _try_execute(
            db,
            """
            ALTER TABLE notification_recipients
              ADD COLUMN inventory_column varchar(80) NULL
                COMMENT '在庫列スコープ（INVENTORY_STAGNATION 用）'
                AFTER machine_cd
            """,
            "notification_recipients.inventory_column",
        )
        await _try_execute(
            db,
            """
            INSERT INTO notification_settings
              (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled, is_active)
            VALUES
              ('INVENTORY_STAGNATION', '在庫停滞アラート', '在庫停滞監視で検出した工程別停滞在庫の通知', 0, 1, 0, 1, 1)
            ON DUPLICATE KEY UPDATE event_name = VALUES(event_name), description = VALUES(description)
            """,
            "notification_settings INVENTORY_STAGNATION",
        )
        await _try_execute(
            db,
            """
            INSERT INTO email_templates (code, name, subject, body, event_code, language, variables, is_active)
            VALUES (
              'INVENTORY_STAGNATION',
              '在庫停滞アラート',
              '【Smart-EMAP】{process_label} 在庫停滞アラート {as_of}（{item_count}件）',
              '<p>{process_label}工程で在庫停滞が検出されました。</p><p>基準日: {as_of}<br>閾値(&gt;): {min_quantity}<br>連続暦日: {stable_calendar_days} 日<br>検出件数: {item_count} 件<br>送信者: {sent_by}<br>送信日時: {sent_at}</p>{item_table}<p>Smart-EMAP 生産管理システム</p>',
              'INVENTORY_STAGNATION',
              'ja',
              '["process_label","as_of","min_quantity","stable_calendar_days","item_count","item_table","item_list_text","sent_by","sent_at"]',
              1
            )
            ON DUPLICATE KEY UPDATE name = VALUES(name), subject = VALUES(subject), body = VALUES(body), variables = VALUES(variables)
            """,
            "email_templates INVENTORY_STAGNATION",
        )
        await _try_execute(
            db,
            """
            ALTER TABLE notification_settings
              ADD COLUMN auto_schedule_enabled tinyint(1) NOT NULL DEFAULT 0
                COMMENT '自動スケジュール有効' AFTER is_active
            """,
            "notification_settings.auto_schedule_enabled",
        )
        await _try_execute(
            db,
            """
            ALTER TABLE notification_settings
              ADD COLUMN auto_schedule_time time NULL DEFAULT NULL
                COMMENT '自動実行時刻（JST）' AFTER auto_schedule_enabled
            """,
            "notification_settings.auto_schedule_time",
        )
        await _try_execute(
            db,
            """
            ALTER TABLE notification_settings
              ADD COLUMN schedule_config json NULL
                COMMENT '自動実行パラメータ JSON' AFTER auto_schedule_time
            """,
            "notification_settings.schedule_config",
        )
        await _try_execute(
            db,
            """
            UPDATE notification_settings
            SET
              auto_schedule_enabled = 1,
              auto_schedule_time = '08:00:00',
              schedule_config = JSON_OBJECT('min_quantity', 50, 'stable_calendar_days', 7)
            WHERE event_code = 'INVENTORY_STAGNATION'
            """,
            "notification_settings schedule defaults",
        )
        await db.commit()
    print("Migrations 53/54 applied.")


if __name__ == "__main__":
    asyncio.run(main())
