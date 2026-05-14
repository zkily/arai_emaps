"""バックアップ保存ディレクトリ解決（API・自動バックアップで共用）。"""
from __future__ import annotations

from typing import Optional

from app.core.config import settings as app_config
from app.services.mysql_backup import is_windows_posix_backup_placeholder, normalize_backup_storage_path


def final_backup_storage_dir(raw: Optional[str]) -> str:
    """
    DB の storage_path が空・無効プレースホルダのときは BACKUP_DEFAULT_STORAGE_PATH を使う。
    """
    rp = (raw or "").strip()
    if is_windows_posix_backup_placeholder(rp):
        rp = ""
    return normalize_backup_storage_path(rp or app_config.BACKUP_DEFAULT_STORAGE_PATH)
