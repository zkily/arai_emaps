"""Apply migration 110: production_review_capacity.target_month (idempotent)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402


async def main() -> None:
    async with AsyncSessionLocal() as db:
        cols = (
            await db.execute(
                text(
                    """
                    SELECT COLUMN_NAME
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'production_review_capacity'
                      AND COLUMN_NAME = 'target_month'
                    """
                )
            )
        ).fetchall()
        if cols:
            print("OK: target_month already exists")
        else:
            await db.execute(
                text(
                    """
                    ALTER TABLE `production_review_capacity`
                      ADD COLUMN `target_month` varchar(7)
                        CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                        NOT NULL DEFAULT ''
                        COMMENT '対象月 YYYY-MM（空=デフォルト）'
                        AFTER `id`
                    """
                )
            )
            print("OK: added target_month column")

        await db.execute(
            text(
                """
                UPDATE `production_review_capacity`
                SET `target_month` = ''
                WHERE `target_month` IS NULL
                """
            )
        )

        idx_rows = (
            await db.execute(
                text(
                    """
                    SELECT INDEX_NAME
                    FROM information_schema.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'production_review_capacity'
                      AND INDEX_NAME IN ('uk_prc_process_cd', 'uk_prc_month_process')
                    """
                )
            )
        ).fetchall()
        names = {r[0] for r in idx_rows}

        if "uk_prc_process_cd" in names:
            await db.execute(text("ALTER TABLE `production_review_capacity` DROP INDEX `uk_prc_process_cd`"))
            print("OK: dropped uk_prc_process_cd")

        if "uk_prc_month_process" not in names:
            await db.execute(
                text(
                    """
                    ALTER TABLE `production_review_capacity`
                      ADD UNIQUE KEY `uk_prc_month_process` (`target_month`, `process_cd`)
                    """
                )
            )
            print("OK: added uk_prc_month_process")

        idx2 = (
            await db.execute(
                text(
                    """
                    SELECT INDEX_NAME
                    FROM information_schema.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'production_review_capacity'
                      AND INDEX_NAME = 'idx_prc_target_month'
                    """
                )
            )
        ).fetchall()
        if not idx2:
            await db.execute(
                text(
                    "ALTER TABLE `production_review_capacity` ADD KEY `idx_prc_target_month` (`target_month`)"
                )
            )
            print("OK: added idx_prc_target_month")

        await db.commit()
    print("Migration 110 applied.")


if __name__ == "__main__":
    asyncio.run(main())
