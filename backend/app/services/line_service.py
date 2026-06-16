"""LINE Messaging API プッシュ送信"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
from dataclasses import dataclass

import httpx
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.system.settings_models import IntegrationConfig

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
# Messaging API の userId（U + 32桁16進）。LINE 名・電話番号・@表示名は不可。
LINE_USER_ID_RE = re.compile(r"^U[a-fA-F0-9]{32}$")


def normalize_line_user_id(line_user_id: str) -> str:
    uid = (line_user_id or "").strip()
    if not uid:
        raise ValueError("LINE User ID が空です")
    if not LINE_USER_ID_RE.match(uid):
        raise ValueError(
            "LINE User ID の形式が不正です。"
            "「U」で始まる33文字の ID を指定してください（例: U1234567890abcdef...）。"
            "LINE の表示名・電話番号・メールアドレスは使用できません。"
        )
    return uid


def is_valid_line_user_id(line_user_id: str) -> bool:
    try:
        normalize_line_user_id(line_user_id)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class LineConfig:
    channel_token: str
    channel_secret: str | None = None
    test_line_user_id: str | None = None


@dataclass
class LineSendResult:
    line_user_id: str
    success: bool
    error: str | None = None


def verify_line_webhook_signature(channel_secret: str, body: bytes, signature: str) -> bool:
    """LINE Webhook の X-Line-Signature を検証する。"""
    if not channel_secret or not signature:
        return False
    mac = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected, signature)


async def load_line_channel_secret(db: AsyncSession) -> str | None:
    """integration_configs（line）から Channel Secret を取得。"""
    result = await db.execute(
        select(IntegrationConfig).where(IntegrationConfig.service_type == "line")
    )
    row = result.scalar_one_or_none()
    if not row or not row.config:
        return None
    secret = (row.config.get("channel_secret") or "").strip()
    return secret or None


async def load_line_config(db: AsyncSession) -> LineConfig | None:
    result = await db.execute(
        select(IntegrationConfig).where(IntegrationConfig.service_type == "line")
    )
    row = result.scalar_one_or_none()
    if not row or not row.is_enabled or not row.config:
        return None
    cfg = row.config
    token = (cfg.get("channel_token") or "").strip()
    if not token:
        return None
    test_id = (cfg.get("test_line_user_id") or "").strip() or None
    secret = (cfg.get("channel_secret") or "").strip() or None
    return LineConfig(channel_token=token, channel_secret=secret, test_line_user_id=test_id)


def html_to_plain_text(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<tr[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</t[dh]>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def push_line_text_message(
    line_config: LineConfig,
    line_user_id: str,
    text: str,
) -> LineSendResult:
    uid = (line_user_id or "").strip()
    if not uid:
        return LineSendResult(line_user_id=line_user_id, success=False, error="LINE User ID が空です")
    try:
        uid = normalize_line_user_id(uid)
    except ValueError as exc:
        return LineSendResult(line_user_id=line_user_id, success=False, error=str(exc))
    body = (text or "").strip()
    if not body:
        return LineSendResult(line_user_id=uid, success=False, error="メッセージが空です")
    if len(body) > 5000:
        body = body[:4997] + "..."
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                LINE_PUSH_URL,
                headers={
                    "Authorization": f"Bearer {line_config.channel_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": uid,
                    "messages": [{"type": "text", "text": body}],
                },
            )
        if resp.status_code == 200:
            return LineSendResult(line_user_id=uid, success=True)
        detail = resp.text
        try:
            detail = resp.json().get("message", detail)
        except Exception:
            pass
        logger.warning("LINE push failed uid={} status={} detail={}", uid, resp.status_code, detail)
        return LineSendResult(line_user_id=uid, success=False, error=f"HTTP {resp.status_code}: {detail}")
    except Exception as exc:
        logger.warning("LINE push exception uid={} err={}", uid, exc)
        return LineSendResult(line_user_id=uid, success=False, error=str(exc))
