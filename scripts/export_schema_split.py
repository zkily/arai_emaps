"""
既存 DB のスキーマを「1 オブジェクト 1 ファイル」で backend/database/schema/ に書き出す。

出力構成:
    schema/tables/<table>.sql        CREATE TABLE IF NOT EXISTS（外部キー含む）
    schema/views/<view>.sql          CREATE OR REPLACE VIEW
    schema/functions/<name>.sql      DROP + CREATE FUNCTION
    schema/procedures/<name>.sql     DROP + CREATE PROCEDURE
    schema/triggers/<name>.sql       DROP + CREATE TRIGGER
    schema/events/<name>.sql         DROP + CREATE EVENT
    schema/seed/<table>.sql          初期データ（INSERT IGNORE）

DEFINER・AUTO_INCREMENT 値・スキーマ名修飾は除去する。
各サブフォルダは毎回作り直すため、DB から消えたオブジェクトのファイルも消える。

用法（リポジトリルートで、backend/.env の DB 接続情報を使用）:

    py scripts/export_schema_split.py --source-db eams_schema_tmp
    py scripts/export_schema_split.py --source-db eams_schema_tmp --exclude cards --exclude decks
    py scripts/export_schema_split.py --source-db eams_schema_tmp --no-seed
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import pymysql

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from bootstrap_full_database import load_db_settings  # noqa: E402

SCHEMA_DIR = ROOT / "backend" / "database" / "schema"
SUBDIRS = ("tables", "views", "functions", "procedures", "triggers", "events", "seed")
# users の開発用管理者は backend/database/init/01_init.sql で投入する
DEFAULT_SEED_SKIP = {"users"}

DEFINER_RE = re.compile(r"\s+DEFINER\s*=\s*`[^`]*`@`[^`]*`", re.IGNORECASE)
AUTO_INC_RE = re.compile(r"\s+AUTO_INCREMENT=\d+")


def _strip_schema(sql: str, db: str) -> str:
    return sql.replace(f"`{db}`.", "")


def _write(path: Path, header: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"{header}\n{body.rstrip()}\n".replace("\r\n", "\n")
    path.write_text(text, encoding="utf-8", newline="\n")


def _header(kind: str, name: str) -> str:
    return f"-- {kind}: {name}\n-- 生成元: scripts/export_schema_split.py\nSET NAMES utf8mb4;\n"


def _delimited(drop: str, create: str) -> str:
    return f"{drop}\n\nDELIMITER $$\n{create.rstrip().rstrip(';')}$$\nDELIMITER ;\n"


def export_tables(cur, db: str, exclude: set[str]) -> list[str]:
    cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
    names = sorted(r[0] for r in cur.fetchall() if r[0] not in exclude)
    for t in names:
        cur.execute(f"SHOW CREATE TABLE `{t}`")
        ddl = AUTO_INC_RE.sub("", cur.fetchone()[1])
        ddl = ddl.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", 1)
        body = f"SET FOREIGN_KEY_CHECKS = 0;\n\n{_strip_schema(ddl, db)};\n\nSET FOREIGN_KEY_CHECKS = 1;"
        _write(SCHEMA_DIR / "tables" / f"{t}.sql", _header("TABLE", t), body)
    return names


def export_views(cur, db: str, exclude: set[str]) -> list[str]:
    cur.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
    names = sorted(r[0] for r in cur.fetchall() if r[0] not in exclude)
    for v in names:
        cur.execute(f"SHOW CREATE VIEW `{v}`")
        ddl = DEFINER_RE.sub("", cur.fetchone()[1])
        ddl = re.sub(r"\s+SQL SECURITY DEFINER", "", ddl)
        ddl = re.sub(r"^CREATE\s+(ALGORITHM=\w+\s+)?", "CREATE OR REPLACE ", ddl)
        _write(SCHEMA_DIR / "views" / f"{v}.sql", _header("VIEW", v), f"{_strip_schema(ddl, db)};")
    return names


def export_routines(cur, db: str, exclude: set[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"FUNCTION": [], "PROCEDURE": []}
    cur.execute(
        "SELECT routine_type, routine_name FROM information_schema.routines "
        "WHERE routine_schema = %s ORDER BY routine_name",
        (db,),
    )
    for kind, name in cur.fetchall():
        if name in exclude:
            continue
        cur.execute(f"SHOW CREATE {kind} `{name}`")
        create = _strip_schema(DEFINER_RE.sub("", cur.fetchone()[2]), db)
        sub = "functions" if kind == "FUNCTION" else "procedures"
        body = _delimited(f"DROP {kind} IF EXISTS `{name}`;", create)
        _write(SCHEMA_DIR / sub / f"{name}.sql", _header(kind, name), body)
        out[kind].append(name)
    return out


def export_triggers(cur, db: str, exclude: set[str]) -> list[str]:
    cur.execute(
        "SELECT trigger_name, event_object_table FROM information_schema.triggers "
        "WHERE trigger_schema = %s ORDER BY trigger_name",
        (db,),
    )
    names = []
    for name, table in cur.fetchall():
        if name in exclude or table in exclude:
            continue
        cur.execute(f"SHOW CREATE TRIGGER `{name}`")
        create = _strip_schema(DEFINER_RE.sub("", cur.fetchone()[2]), db)
        body = _delimited(f"DROP TRIGGER IF EXISTS `{name}`;", create)
        _write(SCHEMA_DIR / "triggers" / f"{name}.sql", _header(f"TRIGGER ({table})", name), body)
        names.append(name)
    return names


def export_events(cur, db: str, exclude: set[str]) -> list[str]:
    cur.execute(
        "SELECT event_name FROM information_schema.events WHERE event_schema = %s ORDER BY event_name",
        (db,),
    )
    names = [r[0] for r in cur.fetchall() if r[0] not in exclude]
    for name in names:
        cur.execute(f"SHOW CREATE EVENT `{name}`")
        create = _strip_schema(DEFINER_RE.sub("", cur.fetchone()[3]), db)
        body = _delimited(f"DROP EVENT IF EXISTS `{name}`;", create)
        _write(SCHEMA_DIR / "events" / f"{name}.sql", _header("EVENT", name), body)
    return names


def export_seed(conn, cur, db: str, tables: list[str], skip: set[str]) -> list[str]:
    written = []
    for t in tables:
        if t in skip:
            continue
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s AND extra NOT LIKE '%%GENERATED%%' "
            "ORDER BY ordinal_position",
            (db, t),
        )
        cols = [r[0] for r in cur.fetchall()]
        col_sql = ", ".join(f"`{c}`" for c in cols)
        cur.execute(f"SELECT {col_sql} FROM `{t}` ORDER BY 1")
        rows = cur.fetchall()
        if not rows:
            continue
        values = ",\n".join("(" + ", ".join(conn.escape(v) for v in row) + ")" for row in rows)
        body = (
            "SET FOREIGN_KEY_CHECKS = 0;\n\n"
            f"INSERT IGNORE INTO `{t}` ({col_sql}) VALUES\n{values};\n\n"
            "SET FOREIGN_KEY_CHECKS = 1;"
        )
        _write(SCHEMA_DIR / "seed" / f"{t}.sql", _header("SEED", t), body)
        written.append(t)
    return written


def export_schema(
    db: str,
    exclude: set[str] | None = None,
    seed: bool = True,
    env_file: Path | None = None,
) -> None:
    host, port, user, password, _ = load_db_settings(env_file)
    exclude = exclude or set()
    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, database=db, charset="utf8mb4"
    )
    try:
        cur = conn.cursor()
        for sub in SUBDIRS:
            shutil.rmtree(SCHEMA_DIR / sub, ignore_errors=True)
        tables = export_tables(cur, db, exclude)
        views = export_views(cur, db, exclude)
        routines = export_routines(cur, db, exclude)
        triggers = export_triggers(cur, db, exclude)
        events = export_events(cur, db, exclude)
        seeds = export_seed(conn, cur, db, tables, DEFAULT_SEED_SKIP) if seed else []
    finally:
        conn.close()

    print(f"Source DB: {db} -> {SCHEMA_DIR.relative_to(ROOT)}")
    print(
        f"  tables={len(tables)} views={len(views)} functions={len(routines['FUNCTION'])} "
        f"procedures={len(routines['PROCEDURE'])} triggers={len(triggers)} events={len(events)} "
        f"seed={len(seeds)}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="DB スキーマを 1 オブジェクト 1 ファイルで書き出す")
    ap.add_argument("--source-db", required=True, help="書き出し元データベース名")
    ap.add_argument("--env-file", type=Path, default=None)
    ap.add_argument(
        "--exclude", action="append", default=[], help="除外するテーブル/ビュー/ルーチン等の名前"
    )
    ap.add_argument("--no-seed", action="store_true", help="初期データ（seed/）を書き出さない")
    args = ap.parse_args()
    export_schema(args.source_db, set(args.exclude), not args.no_seed, args.env_file)


if __name__ == "__main__":
    main()
