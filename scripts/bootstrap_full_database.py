"""
新库一键建库：依次执行 backend/database/init/01_init.sql 与 migrations 下全部 *.sql（按编号排序）。
当前仓库为「全量基线 `02_baseline_full_schema.sql` + 将来可能存在的 `03+_*.sql`（如 `03_xxx.sql`）增量」结构。

依赖：本机已安装 MySQL / MariaDB 客户端，且 mysql 在 PATH 中，或通过 --mysql / MYSQL_BIN 指定。

用法（在仓库根目录，先配置 backend/.env 中的 DB_*）:

    py scripts/bootstrap_full_database.py

可选：

    py scripts/bootstrap_full_database.py --dry-run          # 仅列出将执行的文件
    py scripts/bootstrap_full_database.py --drop-database    # 先 DROP 再 CREATE（危险，仅空库/开发）
    py scripts/bootstrap_full_database.py --mysql "C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe"
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
INIT_SQL = ROOT / "backend" / "database" / "init" / "01_init.sql"
MIGRATIONS_DIR = ROOT / "backend" / "database" / "migrations"
MIGRATION_NUM_RE = re.compile(r"^(\d+)_.*\.sql$")


def _subprocess_kw() -> dict:
    kw: dict = {}
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return kw


def resolve_mysql_executable(preferred: str) -> str:
    pref = (preferred or "").strip() or "mysql"
    if os.path.isfile(pref):
        return os.path.normpath(pref)
    w = shutil.which(pref)
    if w and os.path.isfile(w):
        return w
    for name in ("mysql", "mysql.exe"):
        w = shutil.which(name)
        if w and os.path.isfile(w):
            return w
    if os.name == "nt":
        patterns = [
            r"C:\Program Files\MySQL\*\bin\mysql.exe",
            r"C:\Program Files (x86)\MySQL\*\bin\mysql.exe",
        ]
        found: List[str] = []
        for pat in patterns:
            found.extend(glob.glob(pat))
        existing = [p for p in found if os.path.isfile(p)]
        if existing:
            return max(existing, key=lambda p: os.path.getmtime(p))
    raise RuntimeError(
        "未找到 mysql 客户端。请安装 MySQL / MariaDB Client 并加入 PATH，"
        "或使用 --mysql 指定 mysql.exe 全路径，或设置环境变量 MYSQL_BIN。"
    )


def load_db_settings(env_file: Path | None) -> tuple[str, int, str, str, str]:
    """Minimal .env parser (no python-dotenv dependency for scripts)."""
    paths = []
    if env_file and env_file.is_file():
        paths.append(env_file)
    for p in (ROOT / "backend" / ".env", ROOT / ".env"):
        if p.is_file():
            paths.append(p)
    kv: dict[str, str] = {}
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, _, v = s.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                kv[k] = v
    host = kv.get("DB_HOST", "localhost")
    port_s = kv.get("DB_PORT", "3306")
    user = kv.get("DB_USER", "root")
    password = kv.get("DB_PASSWORD", "")
    db = kv.get("DB_NAME", "eams_db")
    try:
        port = int(port_s)
    except ValueError as e:
        raise SystemExit(f"无效的 DB_PORT: {port_s!r}") from e
    return host, port, user, password, db


def sorted_migration_files() -> List[Path]:
    files = [p for p in MIGRATIONS_DIR.glob("*.sql") if p.is_file()]
    keyed: list[tuple[int, str, Path]] = []
    for p in files:
        m = MIGRATION_NUM_RE.match(p.name)
        if not m:
            raise SystemExit(f"迁移文件名必须以数字前缀命名: {p.name}")
        keyed.append((int(m.group(1)), p.name, p))
    keyed.sort(key=lambda t: (t[0], t[1]))
    return [t[2] for t in keyed]


def write_client_cnf(host: str, port: int, user: str, password: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".cnf", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("[client]\n")
            f.write(f"host={host}\n")
            f.write(f"port={port}\n")
            f.write(f"user={user}\n")
            f.write(f"password={password}\n")
            f.write("default-character-set=utf8mb4\n")
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    return path


def run_mysql(
    mysql_exe: str,
    cnf_path: str,
    args_tail: List[str],
    sql_path: Path | None,
    label: str,
) -> None:
    cmd = [mysql_exe, f"--defaults-extra-file={cnf_path}", *args_tail]
    if sql_path is None:
        r = subprocess.run(cmd, capture_output=True, **_subprocess_kw())
    else:
        with open(sql_path, "rb") as stdin_f:
            r = subprocess.run(cmd, stdin=stdin_f, capture_output=True, **_subprocess_kw())
    if r.returncode != 0:
        err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
        out = (r.stdout or b"").decode("utf-8", errors="replace").strip()
        msg = err or out or f"exit code {r.returncode}"
        raise RuntimeError(f"{label} 失败:\n{msg}")


def main() -> None:
    ap = argparse.ArgumentParser(description="新库一键执行 init + 全部 migrations（mysql 客户端）")
    ap.add_argument("--env-file", type=Path, default=None, help="指定 .env 路径（默认尝试 backend/.env 与仓库根 .env）")
    ap.add_argument("--mysql", default=os.environ.get("MYSQL_BIN", "").strip(), help="mysql 可执行文件路径（默认 PATH / Windows 常见目录）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将执行的 SQL 文件，不连接数据库")
    ap.add_argument(
        "--drop-database",
        action="store_true",
        help="先 DROP DATABASE IF EXISTS 再 CREATE（会删除库内全部数据，仅用于空库/开发）",
    )
    args = ap.parse_args()

    if not INIT_SQL.is_file():
        raise SystemExit(f"缺少 init 脚本: {INIT_SQL}")

    host, port, user, password, db = load_db_settings(args.env_file)
    migrations = sorted_migration_files()

    if args.dry_run:
        print(f"[dry-run] DB={db} host={host} port={port} user={user}")
        print(f"[dry-run] 1. {INIT_SQL.relative_to(ROOT)}")
        for i, p in enumerate(migrations, start=2):
            print(f"[dry-run] {i}. {p.relative_to(ROOT)}")
        print(f"[dry-run] Total: {1 + len(migrations)} SQL file(s)")
        return

    mysql_exe = resolve_mysql_executable(args.mysql)
    cnf_path = write_client_cnf(host, port, user, password)
    try:
        if args.drop_database:
            run_mysql(
                mysql_exe,
                cnf_path,
                ["-e", f"DROP DATABASE IF EXISTS `{db.replace('`', '')}`;"],
                None,
                "DROP DATABASE",
            )
        run_mysql(
            mysql_exe,
            cnf_path,
            [
                "-e",
                f"CREATE DATABASE IF NOT EXISTS `{db.replace('`', '')}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            ],
            None,
            "CREATE DATABASE",
        )
        run_mysql(mysql_exe, cnf_path, [db], INIT_SQL, f"init {INIT_SQL.name}")
        for p in migrations:
            run_mysql(mysql_exe, cnf_path, [db], p, f"migration {p.name}")
    finally:
        try:
            os.unlink(cnf_path)
        except OSError:
            pass

    print(f"Done: database {db!r} — init + {len(migrations)} migration(s) applied.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        raise SystemExit(str(e)) from e
