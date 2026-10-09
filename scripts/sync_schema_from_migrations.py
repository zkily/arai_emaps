"""
把新增的迁移自动同步到 backend/database/schema/（按表拆分的最终结构）。

原理：
    backend/database/schema/synced_migrations.txt 记录已反映到 schema/ 的迁移文件名。
    发现未记录的迁移时：
      1. 用 schema/ 在临时库（默认 eams_schema_sync）建出当前最终结构；
      2. 按编号顺序执行这些新迁移；
      3. 从临时库重新导出 schema/（已有表加列 → 写回该表文件；新表 → 新文件；
         新触发器/过程/初始数据同理），再把文件名追加到 synced_migrations.txt；
      4. 删除临时库。

用法（仓库根目录，使用 backend/.env 的 DB 连接信息，不会改动 DB_NAME 指向的库）:

    py scripts/sync_schema_from_migrations.py              # 同步
    py scripts/sync_schema_from_migrations.py --check      # 只检查，有未同步迁移时退出码 1（不连库）
    py scripts/sync_schema_from_migrations.py --mark-only  # 只登记为已同步（schema/ 已手工改好时）
    py scripts/sync_schema_from_migrations.py --force      # 没有新迁移也重建导出（手工改过 schema/ 后统一格式）
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from bootstrap_full_database import (  # noqa: E402
    SCHEMA_DIR,
    load_db_settings,
    resolve_mysql_executable,
    run_mysql,
    schema_file_groups,
    sorted_migration_files,
    write_client_cnf,
)
from export_schema_split import export_schema  # noqa: E402

SYNCED_LIST = SCHEMA_DIR / "synced_migrations.txt"
ERROR_LINE_RE = re.compile(r"at line (\d+)")


def read_synced() -> set[str]:
    if not SYNCED_LIST.is_file():
        return set()
    return {
        s.strip()
        for s in SYNCED_LIST.read_text(encoding="utf-8").splitlines()
        if s.strip() and not s.startswith("#")
    }


def append_synced(names: list[str]) -> None:
    with SYNCED_LIST.open("a", encoding="utf-8", newline="\n") as f:
        for n in names:
            f.write(f"{n}\n")


def pending_migrations() -> list[Path]:
    synced = read_synced()
    return [p for p in sorted_migration_files() if p.name not in synced]


def build_from_schema(mysql_exe: str, cnf_path: str, db: str) -> None:
    """视图以外的文件合并成一次执行（快）；出错时按行号反查是哪个文件。视图逐个执行并重试依赖。"""
    chunks: list[str] = []
    starts: list[tuple[int, Path]] = []
    line = 1
    views: list[Path] = []
    for sub, files in schema_file_groups():
        if sub == "views":
            views = files
            continue
        for p in files:
            text = p.read_text(encoding="utf-8").rstrip("\n") + "\n"
            starts.append((line, p))
            chunks.append(text)
            line += text.count("\n")

    fd, combined = tempfile.mkstemp(suffix=".sql")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(chunks))
        try:
            run_mysql(mysql_exe, cnf_path, [db], Path(combined), "schema")
        except RuntimeError as e:
            m = ERROR_LINE_RE.search(str(e))
            if m:
                err_line = int(m.group(1))
                src = [p for start, p in starts if start <= err_line][-1]
                raise RuntimeError(f"{src.relative_to(ROOT)} 执行失败:\n{e}") from e
            raise
    finally:
        os.unlink(combined)

    pending = views
    while pending:
        failed: list[tuple[Path, RuntimeError]] = []
        for p in pending:
            try:
                run_mysql(mysql_exe, cnf_path, [db], p, f"schema views/{p.name}")
            except RuntimeError as e:
                failed.append((p, e))
        if len(failed) == len(pending):
            raise failed[0][1]
        pending = [p for p, _ in failed]


def main() -> None:
    ap = argparse.ArgumentParser(description="把新增迁移同步到 backend/database/schema/")
    ap.add_argument("--check", action="store_true", help="只检查是否有未同步迁移（不连库）")
    ap.add_argument("--mark-only", action="store_true", help="不连库，只把未同步迁移登记为已同步")
    ap.add_argument("--tmp-db", default="eams_schema_sync", help="临时库名（会被 DROP 重建）")
    ap.add_argument("--force", action="store_true", help="没有未同步迁移时也重建并导出")
    ap.add_argument("--keep-db", action="store_true", help="结束后保留临时库，便于排查")
    ap.add_argument("--env-file", type=Path, default=None)
    ap.add_argument("--mysql", default=os.environ.get("MYSQL_BIN", "").strip())
    args = ap.parse_args()

    pending = pending_migrations()
    if not pending and (args.check or not args.force):
        print("schema/ 已是最新，没有未同步的迁移。")
        return
    if pending:
        print("未同步的迁移:")
        for p in pending:
            print(f"  {p.name}")
    if args.check:
        sys.exit(1)
    if args.mark_only:
        append_synced([p.name for p in pending])
        print(f"已登记 {len(pending)} 个迁移为已同步（schema/ 未改动）。")
        return

    host, port, user, password, main_db = load_db_settings(args.env_file)
    db = args.tmp_db.replace("`", "")
    if db == main_db:
        raise SystemExit(f"--tmp-db 不能与 DB_NAME 相同: {db}")

    mysql_exe = resolve_mysql_executable(args.mysql)
    cnf_path = write_client_cnf(host, port, user, password)
    try:
        run_mysql(mysql_exe, cnf_path, ["-e", f"DROP DATABASE IF EXISTS `{db}`;"], None, "DROP")
        run_mysql(
            mysql_exe,
            cnf_path,
            [
                "-e",
                f"CREATE DATABASE `{db}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            ],
            None,
            "CREATE",
        )
        build_from_schema(mysql_exe, cnf_path, db)
        for p in pending:
            run_mysql(mysql_exe, cnf_path, [db], p, f"migration {p.name}")
        export_schema(db, env_file=args.env_file)
        if pending:
            append_synced([p.name for p in pending])
        print(f"已同步 {len(pending)} 个迁移到 {SCHEMA_DIR.relative_to(ROOT)}。")
    finally:
        if not args.keep_db:
            try:
                run_mysql(
                    mysql_exe, cnf_path, ["-e", f"DROP DATABASE IF EXISTS `{db}`;"], None, "DROP"
                )
            except RuntimeError as e:
                print(f"临时库 {db} 删除失败: {e}", file=sys.stderr)
        os.unlink(cnf_path)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        raise SystemExit(str(e)) from e
