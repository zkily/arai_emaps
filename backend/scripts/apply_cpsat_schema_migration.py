"""Apply migration 120_cpsat_schema.sql (idempotent ALTERs + CREATE TABLE)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import AsyncSessionLocal  # noqa: E402

MIGRATION_FILE = BACKEND_ROOT / "database" / "migrations" / "120_cpsat_schema.sql"


async def _try_execute(db, stmt: str, label: str) -> None:
    try:
        await db.execute(text(stmt))
        print(f"OK: {label}")
    except Exception as exc:
        err = str(exc)
        if "Duplicate column name" in err or "1060" in err:
            print(f"SKIP (exists): {label}")
            return
        if "already exists" in err.lower() or "1050" in err:
            print(f"SKIP (exists): {label}")
            return
        raise


def _extract_create_tables(sql: str) -> list[str]:
    chunks: list[str] = []
    buf: list[str] = []
    capturing = False
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("CREATE TABLE"):
            capturing = True
            buf = [line]
            continue
        if capturing:
            buf.append(line)
            if stripped.endswith(";"):
                chunks.append("\n".join(buf).rstrip(";").strip())
                capturing = False
                buf = []
    return chunks


async def main() -> None:
    sql = MIGRATION_FILE.read_text(encoding="utf-8")
    async with AsyncSessionLocal() as db:
        await _try_execute(
            db,
            """
            ALTER TABLE process_route_steps
              ADD COLUMN wait_sec_after INT NOT NULL DEFAULT 0
              COMMENT '後工程開始までの最小待ち秒（T_wait）' AFTER cycle_sec
            """,
            "process_route_steps.wait_sec_after",
        )
        await _try_execute(
            db,
            """
            ALTER TABLE product_route_steps
              ADD COLUMN yield_percent DECIMAL(5,2) NULL DEFAULT NULL
              COMMENT '歩留(%)。NULL時は工程ルート/工程マスタ' AFTER process_cd
            """,
            "product_route_steps.yield_percent",
        )
        await _try_execute(
            db,
            """
            ALTER TABLE product_route_steps
              ADD COLUMN wait_sec_after INT NULL DEFAULT NULL
              COMMENT '後工程開始までの最小待ち秒。NULL時は工程ルート既定' AFTER yield_percent
            """,
            "product_route_steps.wait_sec_after",
        )
        await _try_execute(
            db,
            """
            ALTER TABLE machines
              ADD COLUMN use_in_cpsat TINYINT(1) NOT NULL DEFAULT 1
              COMMENT 'CP-SAT自動排程に参加するか' AFTER status
            """,
            "machines.use_in_cpsat",
        )
        await _try_execute(
            db,
            """
            ALTER TABLE product_route_step_machines
              MODIFY COLUMN process_time_sec DECIMAL(10, 2) NOT NULL DEFAULT 0.00
              COMMENT '1本あたり加工時間(秒)。バッチ加工時間 P は数量×本秒で算出'
            """,
            "product_route_step_machines.process_time_sec",
        )
        await _try_execute(
            db,
            """
            UPDATE product_route_steps prs
            LEFT JOIN process_route_steps t
              ON t.route_cd = prs.route_cd AND t.process_cd = prs.process_cd
            LEFT JOIN processes proc
              ON proc.process_cd = prs.process_cd
            SET prs.yield_percent = COALESCE(t.yield_percent, proc.default_yield * 100, 100)
            WHERE prs.yield_percent IS NULL
            """,
            "backfill product_route_steps.yield_percent",
        )
        await _try_execute(
            db,
            """
            UPDATE product_route_steps
            SET wait_sec_after = 0
            WHERE wait_sec_after IS NULL
            """,
            "backfill product_route_steps.wait_sec_after",
        )

        for stmt in _extract_create_tables(sql):
            name = "CREATE TABLE"
            for line in stmt.splitlines():
                if "CREATE TABLE" in line.upper():
                    name = line.strip()[:90]
                    break
            await _try_execute(db, stmt, name)

        await db.commit()
    print("Applied 120_cpsat_schema.sql")


if __name__ == "__main__":
    asyncio.run(main())
