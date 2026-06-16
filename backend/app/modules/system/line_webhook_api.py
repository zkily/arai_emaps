"""LINE Webhook 受信（User ID 收集・自动写入受信者表）"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.modules.system.settings_models import NotificationRecipient, NotificationSetting
from app.services.line_service import load_line_channel_secret, verify_line_webhook_signature

router = APIRouter(tags=["LINE Webhook"])


@router.post("/line/webhook", summary="LINE Webhook（User ID 収集）")
async def line_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    LINE Messaging API Webhook。
    follow / message 等のイベントから source.userId を取得し、line_enabled のイベントに自動登録する。
    """
    body = await request.body()
    signature = request.headers.get("X-Line-Signature") or request.headers.get("x-line-signature")

    channel_secret = await load_line_channel_secret(db)
    if not channel_secret:
        logger.error("[LINE Webhook] Channel Secret 未設定（通知センター → 外部連携 → LINE で保存）")
        raise HTTPException(status_code=400, detail="LINE Channel Secret が未設定です")

    if not signature or not verify_line_webhook_signature(channel_secret, body, signature):
        logger.warning("[LINE Webhook] 署名検証失敗")
        raise HTTPException(status_code=400, detail="Invalid LINE signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    collected: list[str] = []
    for event in payload.get("events") or []:
        source = event.get("source") or {}
        user_id = (source.get("userId") or "").strip()
        event_type = event.get("type") or "unknown"
        if not user_id:
            continue
        collected.append(user_id)
        logger.info(
            "[LINE Webhook] userId={} event={} → notification_recipients（LINE）に自動登録",
            user_id,
            event_type,
        )
        print(f"[LINE Webhook] userId={user_id} event={event_type}", flush=True)

    if not collected:
        logger.info("[LINE Webhook] イベント受信（userId なし） payload_keys={}", list(payload.keys()))

    # line_enabled のイベントコード一覧を取得し、受信者表へ upsert
    event_codes: list[str] = []
    event_res = await db.execute(
        select(NotificationSetting.event_code).where(
            NotificationSetting.is_active.is_(True),
            NotificationSetting.line_enabled.is_(True),
        )
    )
    event_codes = event_res.scalars().all()

    inserted = 0
    for user_id in set(collected):
        for event_code in event_codes:
            exists_res = await db.execute(
                select(NotificationRecipient.id).where(
                    NotificationRecipient.event_code == event_code,
                    NotificationRecipient.recipient_type == "line",
                    NotificationRecipient.line_user_id == user_id,
                )
            )
            exists_id = exists_res.scalar_one_or_none()
            if exists_id:
                continue

            db.add(
                NotificationRecipient(
                    event_code=event_code,
                    recipient_type="line",
                    line_user_id=user_id,
                    is_active=True,
                )
            )
            logger.info(
                "[LINE Webhook] insert recipient: uid={} event_code={}",
                user_id,
                event_code,
            )
            inserted += 1

    if inserted > 0:
        await db.commit()

    return {"ok": True, "user_ids": collected, "inserted": inserted}
