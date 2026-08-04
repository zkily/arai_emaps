"""Apply migration 111 for shipping_long_stay_uninspected_stock (idempotent)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402

MIGRATION_SQL = (
    BACKEND_ROOT / "database" / "migrations" / "111_shipping_long_stay_uninspected_stock.sql"
).read_text(encoding="utf-8")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        for stmt in MIGRATION_SQL.split(";"):
            cleaned = stmt.strip()
            if not cleaned or cleaned.startswith("--"):
                continue
            if cleaned.upper().startswith("SET "):
                await db.execute(text(cleaned))
                continue
            if "CREATE TABLE" in cleaned.upper():
                await db.execute(text(cleaned))
                print("OK: shipping_long_stay_uninspected_stock")
        await db.commit()
    print("Migration 111 applied.")


if __name__ == "__main__":
    asyncio.run(main())
