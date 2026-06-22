"""Apply migration 59_user_todos.sql to an existing database."""
from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

MIGRATION_FILE = Path(__file__).resolve().parents[1] / "database" / "migrations" / "59_user_todos.sql"


async def main() -> None:
    sql = MIGRATION_FILE.read_text(encoding="utf-8")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        for statement in sql.split(";"):
            chunk = statement.strip()
            if chunk:
                await conn.execute(text(chunk))
    await engine.dispose()
    print("Applied 59_user_todos.sql")


if __name__ == "__main__":
    asyncio.run(main())
