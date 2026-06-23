"""Apply migration 60_report_system.sql to an existing database."""
from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

MIGRATION_FILE = Path(__file__).resolve().parents[1] / "database" / "migrations" / "60_report_system.sql"


async def main() -> None:
    sql = MIGRATION_FILE.read_text(encoding="utf-8")
    engine = create_async_engine(settings.get_database_url(), echo=True)
    async with engine.begin() as conn:
        for statement in sql.split(";"):
            chunk = statement.strip()
            if chunk:
                await conn.execute(text(chunk))
    await engine.dispose()
    print("Applied 60_report_system.sql")


if __name__ == "__main__":
    asyncio.run(main())
