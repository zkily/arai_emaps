"""メール送信サービス（SMTP / integration_configs + .env フォールバック）"""
from __future__ import annotations

import asyncio
import re
import smtplib
from dataclasses import dataclass
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_config
from app.modules.system.settings_models import EmailTemplate, IntegrationConfig


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    from_address: str
    use_tls: bool


@dataclass
class EmailSendResult:
    email: str
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class EmailAttachment:
    """メール添付（PDF / Excel など）。"""

    filename: str
    content: bytes
    mime_type: str = "application/octet-stream"


def render_template(template: str, variables: dict[str, Any]) -> str:
    """{key} 形式のプレースホルダを置換する。"""

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        val = variables.get(key, "")
        return "" if val is None else str(val)

    return re.sub(r"\{(\w+)\}", _replace, template)


async def load_smtp_config(db: AsyncSession) -> SmtpConfig | None:
    result = await db.execute(
        select(IntegrationConfig).where(IntegrationConfig.service_type == "smtp")
    )
    row = result.scalar_one_or_none()
    if row and row.is_enabled and row.config:
        cfg = row.config
        host = (cfg.get("host") or "").strip()
        from_addr = (cfg.get("from_address") or cfg.get("from") or "").strip()
        if host and from_addr:
            return SmtpConfig(
                host=host,
                port=int(cfg.get("port") or 587),
                username=(cfg.get("username") or "").strip(),
                password=(cfg.get("password") or "").strip(),
                from_address=from_addr,
                use_tls=bool(cfg.get("use_tls", True)),
            )

    host = (app_config.SMTP_HOST or "").strip()
    from_addr = (app_config.SMTP_FROM or app_config.SMTP_USER or "").strip()
    if not host or not from_addr:
        return None
    return SmtpConfig(
        host=host,
        port=int(app_config.SMTP_PORT or 587),
        username=(app_config.SMTP_USER or "").strip(),
        password=(app_config.SMTP_PASSWORD or "").strip(),
        from_address=from_addr,
        use_tls=bool(app_config.SMTP_USE_TLS),
    )


async def load_email_template(db: AsyncSession, event_code: str) -> EmailTemplate | None:
    result = await db.execute(
        select(EmailTemplate).where(
            EmailTemplate.event_code == event_code,
            EmailTemplate.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


def _send_smtp_sync(
    smtp: SmtpConfig,
    to_email: str,
    subject: str,
    html_body: str,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp.from_address
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if smtp.use_tls:
        server = smtplib.SMTP(smtp.host, smtp.port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
    else:
        server = smtplib.SMTP(smtp.host, smtp.port, timeout=30)
    try:
        if smtp.username:
            server.login(smtp.username, smtp.password)
        server.sendmail(smtp.from_address, [to_email], msg.as_string())
    finally:
        server.quit()


async def send_html_email(
    smtp: SmtpConfig,
    to_email: str,
    subject: str,
    html_body: str,
) -> EmailSendResult:
    try:
        await asyncio.to_thread(_send_smtp_sync, smtp, to_email, subject, html_body)
        return EmailSendResult(email=to_email, success=True)
    except Exception as exc:
        logger.warning("メール送信失敗 to={} err={}", to_email, exc)
        return EmailSendResult(email=to_email, success=False, error=str(exc))


async def send_bulk_html_email(
    smtp: SmtpConfig,
    recipients: list[str],
    subject: str,
    html_body: str,
) -> list[EmailSendResult]:
    results: list[EmailSendResult] = []
    for email in recipients:
        results.append(await send_html_email(smtp, email, subject, html_body))
    return results


def _send_smtp_with_attachments_sync(
    smtp: SmtpConfig,
    to_email: str,
    subject: str,
    html_body: str,
    attachments: list[EmailAttachment],
) -> None:
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = smtp.from_address
    msg["To"] = to_email

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(body)

    for att in attachments:
        part = MIMEBase(*att.mime_type.split("/", 1)) if "/" in att.mime_type else MIMEBase("application", "octet-stream")
        part.set_payload(att.content)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=("utf-8", "", att.filename),
        )
        msg.attach(part)

    if smtp.use_tls:
        server = smtplib.SMTP(smtp.host, smtp.port, timeout=60)
        server.ehlo()
        server.starttls()
        server.ehlo()
    else:
        server = smtplib.SMTP(smtp.host, smtp.port, timeout=60)
    try:
        if smtp.username:
            server.login(smtp.username, smtp.password)
        server.sendmail(smtp.from_address, [to_email], msg.as_string())
    finally:
        server.quit()


async def send_html_email_with_attachments(
    smtp: SmtpConfig,
    to_email: str,
    subject: str,
    html_body: str,
    attachments: list[EmailAttachment],
) -> EmailSendResult:
    """HTML 本文 + 添付ファイル付きメールを 1 通送信する。"""
    if not attachments:
        return await send_html_email(smtp, to_email, subject, html_body)
    try:
        await asyncio.to_thread(
            _send_smtp_with_attachments_sync, smtp, to_email, subject, html_body, attachments
        )
        return EmailSendResult(email=to_email, success=True)
    except Exception as exc:
        logger.warning("添付メール送信失敗 to={} err={}", to_email, exc)
        return EmailSendResult(email=to_email, success=False, error=str(exc))
