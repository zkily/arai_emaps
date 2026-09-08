"""Apply migration 124_text_label_print_menu.sql (idempotent)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402

MIGRATION_FILE = BACKEND_ROOT / "database" / "migrations" / "124_text_label_print_menu.sql"


async def main() -> None:
    raw = MIGRATION_FILE.read_text(encoding="utf-8")
    sql = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("--"))
    statements = [chunk.strip() for chunk in sql.split(";") if chunk.strip()]
    async with AsyncSessionLocal() as db:
        for stmt in statements:
            await db.execute(text(stmt))
            preview = " ".join(stmt.split())[:90]
            print(f"OK: {preview}")
        await db.commit()
    print("menu MASTER_TEXT_LABEL_PRINT applied")


if __name__ == "__main__":
    asyncio.run(main())
