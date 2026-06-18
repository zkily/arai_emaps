"""在庫停滞アラート自動巡検（日次スケジュール）"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time as time_of_day
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_config
from app.modules.system.settings_models import EmailSendLog, LineSendLog, NotificationSetting
from app.services.full_database_backup import (
    is_past_schedule_today,
    local_now_for_schedule,
    parse_schedule_hh_mm,
    seconds_until_next_schedule,
)
from app.services.inventory_stagnation_notification import (
    EVENT_CODE,
    REFERENCE_PREFIX,
    send_inventory_stagnation_notification,
)

DEFAULT_MIN_QUANTITY = 50
DEFAULT_STABLE_DAYS = 7
DEFAULT_SCHEDULE_TIME = "08:00"


@dataclass(frozen=True)
class AutoPatrolConfig:
    enabled: bool
    schedule_time: str
    min_quantity: int
    stable_calendar_days: int
    catchup_on_start: bool


def _parse_schedule_config(raw: Any) -> tuple[int, int]:
    min_qty = DEFAULT_MIN_QUANTITY
    stable_days = DEFAULT_STABLE_DAYS
    if isinstance(raw, dict):
        try:
            min_qty = int(raw.get("min_quantity", min_qty))
        except (TypeError, ValueError):
            pass
        try:
            stable_days = int(raw.get("stable_calendar_days", stable_days))
        except (TypeError, ValueError):
            pass
    min_qty = max(0, min_qty)
    stable_days = max(2, min(60, stable_days))
    return min_qty, stable_days


def _format_schedule_time(value: time_of_day | None) -> str:
    if value is None:
        return DEFAULT_SCHEDULE_TIME
    return f"{value.hour:02d}:{value.minute:02d}"


async def load_auto_patrol_config(db: AsyncSession) -> AutoPatrolConfig:
    """DB の notification_settings を優先し、未設定時は .env 既定。"""
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.event_code == EVENT_CODE)
    )
    row = result.scalar_one_or_none()

    env_enabled = bool(getattr(app_config, "INVENTORY_STAGNATION_AUTO_ENABLED", False))
    env_time = getattr(app_config, "INVENTORY_STAGNATION_AUTO_TIME", DEFAULT_SCHEDULE_TIME)
    env_min, env_stable = _parse_schedule_config(
        {
            "min_quantity": getattr(app_config, "INVENTORY_STAGNATION_AUTO_MIN_QUANTITY", DEFAULT_MIN_QUANTITY),
            "stable_calendar_days": getattr(
                app_config, "INVENTORY_STAGNATION_AUTO_STABLE_DAYS", DEFAULT_STABLE_DAYS
            ),
        }
    )
    catchup = bool(getattr(app_config, "INVENTORY_STAGNATION_AUTO_CATCHUP_ON_START", True))

    if not row:
        return AutoPatrolConfig(
            enabled=env_enabled,
            schedule_time=env_time,
            min_quantity=env_min,
            stable_calendar_days=env_stable,
            catchup_on_start=catchup,
        )

    min_qty, stable_days = _parse_schedule_config(row.schedule_config)
    enabled = bool(row.auto_schedule_enabled) if row.auto_schedule_enabled is not None else env_enabled
    schedule_time = _format_schedule_time(row.auto_schedule_time) if row.auto_schedule_time else env_time

    return AutoPatrolConfig(
        enabled=enabled and bool(row.is_active),
        schedule_time=schedule_time,
        min_quantity=min_qty,
        stable_calendar_days=stable_days,
        catchup_on_start=catchup,
    )


async def has_auto_patrol_run_today(db: AsyncSession, *, as_of: str) -> bool:
    """当日・同一基準日の自動巡検が成功送信済みか（いずれかチャネル）。"""
    prefix = f"{REFERENCE_PREFIX}:{as_of}:"
    email_q = await db.execute(
        select(EmailSendLog.id).where(
            EmailSendLog.event_code == EVENT_CODE,
            EmailSendLog.reference_key.like(f"{prefix}%"),
            EmailSendLog.status == "success",
        ).limit(1)
    )
    if email_q.scalar_one_or_none() is not None:
        return True
    line_q = await db.execute(
        select(LineSendLog.id).where(
            LineSendLog.event_code == EVENT_CODE,
            LineSendLog.reference_key.like(f"{prefix}%"),
            LineSendLog.status == "success",
        ).limit(1)
    )
    return line_q.scalar_one_or_none() is not None


async def run_inventory_stagnation_auto_patrol_once(db: AsyncSession) -> dict:
    """自動巡検 1 回実行（エラー時も dict を返し HTTPException は投げない）。"""
    cfg = await load_auto_patrol_config(db)
    if not cfg.enabled:
        return {"success": True, "status": "disabled", "message": "自動巡検は無効です"}

    now_local = local_now_for_schedule()
    as_of = now_local.date().isoformat()

    try:
        result = await send_inventory_stagnation_notification(
            db,
            as_of=as_of,
            min_quantity=cfg.min_quantity,
            stable_calendar_days=cfg.stable_calendar_days,
            inventory_columns=None,
            current_user=None,
            trigger="auto",
        )
        logger.info(
            "在庫停滞自動巡検完了: as_of={} status={} total_sent={}",
            as_of,
            result.get("status"),
            result.get("total_sent", 0),
        )
        return result
    except Exception as exc:
        logger.warning("在庫停滞自動巡検で例外: {}", exc)
        return {"success": False, "status": "error", "message": str(exc)}


async def maybe_catchup_auto_patrol(db: AsyncSession) -> None:
    """起動時：当日の予定時刻を過ぎており、まだ巡検送信が無ければ 1 回実行。"""
    cfg = await load_auto_patrol_config(db)
    if not cfg.enabled or not cfg.catchup_on_start:
        return
    try:
        hour, minute = parse_schedule_hh_mm(cfg.schedule_time)
    except ValueError as exc:
        logger.warning("在庫停滞自動巡検: 時刻設定が無効: {}", exc)
        return

    now_local = local_now_for_schedule()
    if not is_past_schedule_today(now_local, hour, minute):
        return

    as_of = now_local.date().isoformat()
    if await has_auto_patrol_run_today(db, as_of=as_of):
        return

    logger.info("在庫停滞自動巡検: 起動時キャッチアップ実行 as_of={}", as_of)
    await run_inventory_stagnation_auto_patrol_once(db)
