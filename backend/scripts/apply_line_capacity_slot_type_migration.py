"""Apply migration 123_line_capacity_slot_type.sql (idempotent ALTERs)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402

MIGRATION_FILE = BACKEND_ROOT / "database" / "migrations" / "123_line_capacity_slot_type.sql"


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
    raw = MIGRATION_FILE.read_text(encoding="utf-8")
    sql = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("--"))
    statements = [chunk.strip() for chunk in sql.split(";") if chunk.strip()]
    async with AsyncSessionLocal() as db:
        for stmt in statements:
            preview = " ".join(stmt.split())[:90]
            await _try_execute(db, stmt, preview)
        await db.commit()
    print("Applied 123_line_capacity_slot_type.sql")


if __name__ == "__main__":
    asyncio.run(main())
