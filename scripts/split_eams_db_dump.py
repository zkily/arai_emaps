#!/usr/bin/env python3
"""
Split a Navicat-style MySQL dump (e.g. eams_db.sql) into one .sql file per table.

Anything after the last table data (procedures, triggers, events, final SET) is
written to _procedures_triggers_events.sql. Preamble before the first table goes
to _preamble.sql.

Usage:
  python scripts/split_eams_db_dump.py
  python scripts/split_eams_db_dump.py path/to/dump.sql path/to/output_dir
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TABLE_START = re.compile(r"^--\s*Table structure for\s+`?(\w+)`?\s*$")
POST_START = re.compile(
    r"^--\s*(Procedure|Function|Triggers|Event|View)\s+structure"
)

SQL_HEADER = """SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

"""
SQL_FOOTER = """
SET FOREIGN_KEY_CHECKS = 1;
"""


def safe_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError(f"unsafe table name for filesystem: {name!r}")
    return name


def write_file(path: Path, body: str, wrap: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = body
    if wrap:
        text = SQL_HEADER + body.rstrip() + SQL_FOOTER
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    default_src = root / "eams_db.sql"
    default_out = root / "eams_db_tables"

    src = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default_src
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else default_out

    if not src.is_file():
        print(f"Source not found: {src}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)

    preamble: list[str] = []
    current_table: str | None = None
    current_lines: list[str] = []
    post_lines: list[str] = []
    mode = "preamble"  # preamble | table | post
    table_count = 0

    with src.open("r", encoding="utf-8", errors="replace", newline="") as f:
        for line in f:
            if mode == "post":
                post_lines.append(line)
                continue

            if POST_START.match(line):
                if current_table is not None:
                    name = safe_name(current_table)
                    write_file(
                        out_dir / f"{name}.sql",
                        "".join(current_lines),
                        wrap=True,
                    )
                    table_count += 1
                    current_table = None
                    current_lines = []
                mode = "post"
                post_lines.append(line)
                continue

            m = TABLE_START.match(line.rstrip("\r\n"))
            if m:
                if current_table is not None:
                    name = safe_name(current_table)
                    write_file(
                        out_dir / f"{name}.sql",
                        "".join(current_lines),
                        wrap=True,
                    )
                    table_count += 1
                current_table = m.group(1)
                # First table: Navicat puts "-- ----------------------------" before
                # "Table structure for ..."; it was still in preamble — move it in.
                first_chunk: list[str] = []
                if mode == "preamble" and preamble:
                    tail = preamble[-1].rstrip("\r\n")
                    if tail.strip() == "-- ----------------------------":
                        preamble.pop()
                        if preamble and preamble[-1].strip() == "":
                            preamble.pop()
                        first_chunk.append("-- ----------------------------\n")
                current_lines = first_chunk + [line]
                mode = "table"
                continue

            if mode == "preamble":
                preamble.append(line)
            else:
                current_lines.append(line)

    if mode != "post" and current_table is not None:
        name = safe_name(current_table)
        write_file(out_dir / f"{name}.sql", "".join(current_lines), wrap=True)
        table_count += 1

    if preamble:
        write_file(out_dir / "_preamble.sql", "".join(preamble), wrap=False)

    if post_lines:
        write_file(
            out_dir / "_procedures_triggers_events.sql",
            "".join(post_lines),
            wrap=False,
        )

    print(f"Wrote {table_count} table file(s) under {out_dir}")
    if preamble:
        print("Also: _preamble.sql")
    if post_lines:
        print("Also: _procedures_triggers_events.sql")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
