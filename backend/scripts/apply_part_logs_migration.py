"""Apply migration 58 for part_logs table (idempotent)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402

MIGRATION_SQL = (BACKEND_ROOT / "database" / "migrations" / "58_part_logs.sql").read_text(
    encoding="utf-8"
)


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(text(MIGRATION_SQL))
        await db.commit()
    print("Migration 58 applied: part_logs")


if __name__ == "__main__":
    asyncio.run(main())
