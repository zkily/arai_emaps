"""
全庫 mysqldump バックアップの実行（手動 API・.env 自動バックアップで共用）。
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, time as time_of_day
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_config
from app.modules.system.settings_models import BackupHistory, BackupSetting
from app.services.backup_paths import final_backup_storage_dir
from app.services.mysql_backup import apply_retention, run_mysqldump_to_file

logger = logging.getLogger(__name__)


async def load_backup_run_preferences(db: AsyncSession) -> Tuple[str, int, bool]:
    """BackupSetting 行があれば優先。無いときは .env の DB_AUTO_BACKUP_* 既定を使う。"""
    result = await db.execute(select(BackupSetting).where(BackupSetting.id == 1))
    setting = result.scalar_one_or_none()
    if not setting:
        return (
            final_backup_storage_dir(None),
            int(app_config.DB_AUTO_BACKUP_RETENTION),
            bool(app_config.DB_AUTO_BACKUP_COMPRESS),
        )
    raw_path = (setting.storage_path or "").strip()
    return (
        final_backup_storage_dir(raw_path),
        int(setting.retention_count or app_config.DB_AUTO_BACKUP_RETENTION),
        bool(setting.compression_enabled),
    )


def parse_schedule_hh_mm(value: str) -> Tuple[int, int]:
    s = (value or "").strip()
    parts = s.split(":")
    if len(parts) != 2:
        raise ValueError("HH:MM 形式ではありません")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("時刻が範囲外です")
    return h, m


async def perform_full_database_backup(
    db: AsyncSession,
    *,
    backup_type: str,
    created_by: Optional[int],
    storage_path: str,
    retention: int,
    compress: bool,
) -> Dict[str, Any]:
    """
    mysqldump → ファイル、履歴記録、保持世代による古ファイル削除。
    backup_type: manual / auto
    """
    now = datetime.now()
    ext = ".sql.gz" if compress else ".sql"
    filename = f"backup_{now.strftime('%Y%m%d_%H%M%S')}{ext}"
    full_path = os.path.join(storage_path, filename)

    history = BackupHistory(
        filename=filename,
        file_path=full_path,
        backup_type=backup_type,
        status="running",
        started_at=now,
        created_by=created_by,
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    def _run_dump() -> int:
        os.makedirs(storage_path, exist_ok=True)
        return run_mysqldump_to_file(
            out_path=full_path,
            host=app_config.DB_HOST,
            port=app_config.DB_PORT,
            user=app_config.DB_USER,
            password=app_config.DB_PASSWORD,
            database=app_config.DB_NAME,
            compress=compress,
            mysqldump_bin=(app_config.MYSQLDUMP_BIN or "mysqldump").strip() or "mysqldump",
        )

    try:
        size = await asyncio.to_thread(_run_dump)
    except Exception as e:
        logger.exception("%s backup failed", backup_type)
        history.status = "failed"
        history.error_message = str(e)[:2000]
        history.completed_at = datetime.now()
        await db.commit()
        raise

    history.status = "completed"
    history.file_path = full_path
    history.file_size = size
    history.completed_at = datetime.now()
    await db.commit()

    try:
        await asyncio.to_thread(apply_retention, storage_path, retention)
    except Exception:
        logger.exception("apply_retention failed after %s backup", backup_type)

    logger.info("%s backup OK: %s (%s bytes)", backup_type, full_path, size)
    return {
        "message": "バックアップが完了しました",
        "filename": filename,
        "file_path": full_path,
        "file_size": size,
        "id": history.id,
    }


async def has_successful_auto_backup_today(db: AsyncSession, *, now_local: datetime) -> bool:
    """completed かつ backup_type=auto で、本日（ローカル日付）に完了した履歴があるか。"""
    today_start = datetime(now_local.year, now_local.month, now_local.day)
    q = (
        select(func.count())
        .select_from(BackupHistory)
        .where(
            BackupHistory.backup_type == "auto",
            BackupHistory.status == "completed",
            BackupHistory.completed_at.is_not(None),
            BackupHistory.completed_at >= today_start,
        )
    )
    result = await db.execute(q)
    n = result.scalar() or 0
    return int(n) > 0


def local_now_for_schedule() -> datetime:
    """TIMEZONE（datetime_utils.JST と一致）での現在ローカル時刻（naive・壁時計）。"""
    from app.core.datetime_utils import JST

    return datetime.now(JST).replace(tzinfo=None)


def seconds_until_next_schedule(now_local: datetime, hour: int, minute: int) -> float:
    """次の同一時刻（ローカル日付）までの秒数。最低 1 秒。"""
    target = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now_local >= target:
        from datetime import timedelta

        target = target + timedelta(days=1)
    return max((target - now_local).total_seconds(), 1.0)


def is_past_schedule_today(now_local: datetime, hour: int, minute: int) -> bool:
    return now_local.time() >= time_of_day(hour, minute)
