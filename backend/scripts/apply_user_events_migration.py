"""Apply user_events migrations 142–145 (idempotent)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402

MIGRATION_142 = BACKEND_ROOT / "database" / "migrations" / "142_user_events.sql"

ENHANCE_COLUMNS = [
    ("recurrence_rule", "varchar(20) DEFAULT NULL COMMENT 'daily|weekly|monthly|yearly'"),
    ("recurrence_until", "date DEFAULT NULL COMMENT '繰り返し終了日'"),
    ("remind_offset_minutes", "int DEFAULT NULL COMMENT '事前リマインド分数（NULL=無効）'"),
    ("remind_at", "datetime DEFAULT NULL COMMENT '次回リマインド発火時刻'"),
    ("reminded_at", "datetime DEFAULT NULL COMMENT 'リマインド済み時刻'"),
    ("last_reminded_occurrence", "date DEFAULT NULL COMMENT '繰り返し：最後に確認した発生日'"),
    ("visibility", "varchar(20) NOT NULL DEFAULT 'department' COMMENT 'self=私密 department=部門内'"),
    ("recurrence_exdates", "text DEFAULT NULL COMMENT '除外発生日 JSON'"),
    ("reminded_dates", "text DEFAULT NULL COMMENT '確認済み発生日 JSON'"),
]


async def _table_exists(db, table: str) -> bool:
    result = await db.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = :table"
        ),
        {"table": table},
    )
    return int(result.scalar() or 0) > 0


async def _column_exists(db, table: str, column: str) -> bool:
    result = await db.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    )
    return int(result.scalar() or 0) > 0


async def main() -> None:
    async with AsyncSessionLocal() as db:
        if not await _table_exists(db, "user_events"):
            sql = MIGRATION_142.read_text(encoding="utf-8")
            for statement in sql.split(";"):
                chunk = statement.strip()
                if not chunk or chunk.startswith("--"):
                    continue
                if chunk.upper().startswith("SET "):
                    await db.execute(text(chunk))
                    continue
                await db.execute(text(chunk))
            print("Applied 142_user_events.sql (created user_events)")
        else:
            print("user_events already exists")

        for col_name, col_def in ENHANCE_COLUMNS:
            if await _column_exists(db, "user_events", col_name):
                print(f"  skip column {col_name} (exists)")
                continue
            await db.execute(text(f"ALTER TABLE `user_events` ADD COLUMN `{col_name}` {col_def}"))
            print(f"  added column {col_name}")

        await db.commit()
        print("Applied enhance columns (143-145)")
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
