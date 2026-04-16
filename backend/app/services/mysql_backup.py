"""
MySQL 全库逻辑备份：mysqldump + 可选 gzip。
输出路径支持 Windows UNC（如 \\\\server\\share\\...）。
"""
from __future__ import annotations

import glob
import gzip
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

BACKUP_FILE_RE = re.compile(
    r"^backup_(?P<dt>\d{8}_\d{6})(?P<ext>\.sql\.gz|\.sql)$",
    re.IGNORECASE,
)


def normalize_backup_storage_path(path: str) -> str:
    """
    バックアップ保存ディレクトリを正規化する。
    Windows の UNC（\\\\server\\share\\...）を os.path.normpath 等で先頭の \\\\ が壊れないよう pathlib を使う。
    """
    p = os.path.expandvars((path or "").strip())
    if not p:
        return p
    if os.name == "nt":
        return str(Path(p))
    return os.path.normpath(p)


def is_windows_posix_backup_placeholder(path: str) -> bool:
    """DB に残った Linux 用既定 '/backup/' 等（Windows ではドライブ直下 \\backup になり共有とずれる）。"""
    if os.name != "nt":
        return False
    rp = (path or "").strip().replace("\\", "/").rstrip("/").lower()
    return rp in ("/backup", "/backup/")


def _subprocess_kw() -> dict:
    kw: dict = {}
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return kw


def resolve_mysqldump_executable(preferred: str) -> str:
    """
    mysqldump 実行ファイルのパスを解決する。
    Windows では PATH に無くても Program Files 配下を探索する。
    """
    pref = (preferred or "").strip() or "mysqldump"

    if os.path.isfile(pref):
        return os.path.normpath(pref)

    w = shutil.which(pref)
    if w and os.path.isfile(w):
        return w

    for name in ("mysqldump", "mysqldump.exe"):
        w = shutil.which(name)
        if w and os.path.isfile(w):
            return w

    if os.name == "nt":
        patterns = [
            r"C:\Program Files\MySQL\*\bin\mysqldump.exe",
            r"C:\Program Files (x86)\MySQL\*\bin\mysqldump.exe",
        ]
        found: List[str] = []
        for pat in patterns:
            found.extend(glob.glob(pat))
        existing = [p for p in found if os.path.isfile(p)]
        if existing:
            return max(existing, key=lambda p: os.path.getmtime(p))

    raise RuntimeError(
        "mysqldump が見つかりません（PATH に無い、または MySQL が未インストールの可能性があります）。"
        "対処: (1) MySQL Server または MySQL Shell / Client をインストールする "
        "(2) 環境変数 MYSQLDUMP_BIN に mysqldump.exe のフルパスを設定する。"
        f"例: MYSQLDUMP_BIN=C:\\\\Program Files\\\\MySQL\\\\MySQL Server 8.0\\\\bin\\\\mysqldump.exe "
        f"（現在の設定値: {pref!r}）"
    )


def _build_mysqldump_cmd(
    mysqldump_bin: str,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
) -> List[str]:
    return [
        mysqldump_bin,
        f"--host={host}",
        f"--port={port}",
        f"--user={user}",
        f"--password={password}",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--events",
        "--databases",
        database,
    ]


def run_mysqldump_to_file(
    *,
    out_path: str,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    compress: bool,
    mysqldump_bin: str = "mysqldump",
) -> int:
    """
    执行 mysqldump 并写入 out_path。compress=True 时写入 gzip 压缩流（扩展名建议 .sql.gz）。
    返回写入文件的字节大小。
    """
    exe = resolve_mysqldump_executable(mysqldump_bin)
    cmd = _build_mysqldump_cmd(exe, host, port, user, password, database)
    sub_kw = _subprocess_kw()

    if compress:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **sub_kw,
        )
        stderr = b""
        try:
            assert proc.stdout is not None
            with gzip.open(out_path, "wb", compresslevel=6) as gz:
                shutil.copyfileobj(proc.stdout, gz, length=1024 * 1024)
        finally:
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                stderr = proc.stderr.read() or b""
        code = proc.wait()
        if code != 0:
            try:
                os.remove(out_path)
            except OSError:
                pass
            msg = stderr.decode("utf-8", errors="replace").strip() or f"mysqldump が終了コード {code} で失敗しました"
            raise RuntimeError(msg[:8000])
    else:
        with open(out_path, "wb") as out_f:
            proc = subprocess.run(
                cmd,
                stdout=out_f,
                stderr=subprocess.PIPE,
                **sub_kw,
            )
        if proc.returncode != 0:
            try:
                os.remove(out_path)
            except OSError:
                pass
            msg = (proc.stderr or b"").decode("utf-8", errors="replace").strip() or (
                f"mysqldump が終了コード {proc.returncode} で失敗しました"
            )
            raise RuntimeError(msg[:8000])

    return int(os.path.getsize(out_path))


def apply_retention(storage_dir: str, retention: int) -> None:
    """删除超出保持世代数的 backup_YYYYMMDD_HHMMSS.sql(.gz)（按修改时间保留最新）。"""
    if retention < 1:
        return
    try:
        names = os.listdir(storage_dir)
    except OSError as e:
        logger.warning("バックアップ保持: listdir 失敗 %s: %s", storage_dir, e)
        return

    files: List[Tuple[float, str]] = []
    for name in names:
        if not BACKUP_FILE_RE.match(name):
            continue
        full = os.path.join(storage_dir, name)
        try:
            mtime = os.path.getmtime(full)
        except OSError:
            continue
        files.append((mtime, full))

    files.sort(reverse=True)
    for _, path in files[retention:]:
        try:
            os.remove(path)
            logger.info("バックアップ保持: 削除 %s", path)
        except OSError as e:
            logger.warning("バックアップ保持: 削除不可 %s: %s", path, e)
