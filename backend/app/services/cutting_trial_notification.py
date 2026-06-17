"""切断試作完了通知（備考に「試作」を含み production_completed_check=1 の切断指示）"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.auth.models import User
from app.modules.system.settings_models import EmailSendLog, LineSendLog, NotificationSetting
from app.services.confirm_actual_email import parse_production_day
from app.services.email_service import (
    load_email_template,
    load_smtp_config,
    render_template,
    send_html_email,
)
from app.services.line_service import load_line_config, push_line_text_message
from app.services.notification_recipient_service import (
    resolve_line_recipients,
    resolve_notification_recipients,
)

EVENT_CODE = "CUTTING_TRIAL_COMPLETED"
REFERENCE_PREFIX = "cutting_trial"


async def _get_notification_setting(db: AsyncSession) -> NotificationSetting | None:
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.event_code == EVENT_CODE)
    )
    return result.scalar_one_or_none()


async def _fetch_trial_rows(db: AsyncSession, prod_day: date) -> list[dict]:
    sql = text("""
        SELECT
            production_day,
            product_name,
            product_cd,
            COALESCE(actual_production_quantity, 0) AS actual_production_quantity
        FROM cutting_management
        WHERE production_day = :production_day
          AND production_completed_check = 1
          AND remarks IS NOT NULL
          AND remarks LIKE '%試作%'
        ORDER BY production_sequence ASC, id ASC
    """)
    res = await db.execute(sql, {"production_day": prod_day})
    return [dict(r) for r in res.mappings().fetchall()]


def _format_production_day(val) -> str:
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val or "")


def _build_item_summaries(rows: list[dict]) -> tuple[str, str, int]:
    if not rows:
        return "", "", 0

    html_lines = []
    text_lines = []
    total_qty = 0
    for row in rows:
        day_str = _format_production_day(row.get("production_day"))
        product = (row.get("product_name") or row.get("product_cd") or "—").strip() or "—"
        qty = int(row.get("actual_production_quantity") or 0)
        total_qty += qty
        html_lines.append(
            f"<tr><td>{day_str}</td><td>{product}</td><td align='right'>{qty:,} 本</td></tr>"
        )
        text_lines.append(f"  生産日: {day_str}  製品名: {product}  生産数: {qty:,} 本")

    item_list_html = (
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>生産日</th><th>製品名</th><th>生産数</th></tr>"
        f"{''.join(html_lines)}</table>"
    )
    item_list_text = "明細:\n" + "\n".join(text_lines)
    return item_list_html, item_list_text, total_qty


def _build_variables(
    *,
    prod_day: date,
    rows: list[dict],
    current_user: User,
    sent_at_str: str,
) -> dict:
    item_list_html, item_list_text, total_qty = _build_item_summaries(rows)
    return {
        "production_day": prod_day.isoformat(),
        "item_count": len(rows),
        "total_quantity": f"{total_qty:,}",
        "item_list": item_list_html,
        "item_list_text": item_list_text,
        "sent_by": (current_user.full_name or current_user.username or ""),
        "sent_at": sent_at_str,
    }


async def _already_sent_email(db: AsyncSession, reference_key: str) -> bool:
    log_res = await db.execute(
        select(EmailSendLog).where(
            EmailSendLog.event_code == EVENT_CODE,
            EmailSendLog.reference_key == reference_key,
            EmailSendLog.status == "success",
        )
    )
    return log_res.scalars().first() is not None


async def _already_sent_line(db: AsyncSession, reference_key: str) -> bool:
    log_res = await db.execute(
        select(LineSendLog).where(
            LineSendLog.event_code == EVENT_CODE,
            LineSendLog.reference_key == reference_key,
            LineSendLog.status == "success",
        )
    )
    return log_res.scalars().first() is not None


async def get_cutting_trial_notification_preview(
    db: AsyncSession,
    *,
    production_day: str,
) -> dict:
    prod_day = parse_production_day(production_day)
    reference_key = f"{REFERENCE_PREFIX}:{prod_day.isoformat()}"

    setting = await _get_notification_setting(db)
    email_enabled = bool(setting and setting.is_active and setting.email_enabled)
    line_enabled = bool(setting and setting.is_active and setting.line_enabled)

    rows = await _fetch_trial_rows(db, prod_day)
    _, _, total_qty = _build_item_summaries(rows)

    email_recipients = await resolve_notification_recipients(db, EVENT_CODE)
    line_recipients = await resolve_line_recipients(db, EVENT_CODE)
    template = await load_email_template(db, EVENT_CODE)
    smtp = await load_smtp_config(db)
    line_cfg = await load_line_config(db)

    already_sent_email = await _already_sent_email(db, reference_key)
    already_sent_line = await _already_sent_line(db, reference_key)

    item_count = len(rows)
    can_send_email = email_enabled and smtp is not None and len(email_recipients) > 0 and item_count > 0
    can_send_line = line_enabled and line_cfg is not None and len(line_recipients) > 0 and item_count > 0
    can_send = can_send_email or can_send_line

    already_sent = False
    if email_enabled and line_enabled:
        already_sent = (
            (not can_send_email or already_sent_email)
            and (not can_send_line or already_sent_line)
            and (already_sent_email or already_sent_line)
        )
    elif email_enabled:
        already_sent = already_sent_email
    elif line_enabled:
        already_sent = already_sent_line

    items = [
        {
            "production_day": _format_production_day(r.get("production_day")),
            "product_name": (r.get("product_name") or r.get("product_cd") or "").strip(),
            "production_quantity": int(r.get("actual_production_quantity") or 0),
        }
        for r in rows
    ]

    return {
        "success": True,
        "production_day": prod_day.isoformat(),
        "item_count": item_count,
        "total_quantity": total_qty,
        "items": items,
        "email_enabled": email_enabled,
        "line_enabled": line_enabled,
        "smtp_configured": smtp is not None,
        "line_configured": line_cfg is not None,
        "recipients": [
            {"email": r.email, "name": r.name, "source": r.source} for r in email_recipients
        ],
        "line_recipients": [
            {"line_user_id": r.line_user_id, "name": r.name, "source": r.source}
            for r in line_recipients
        ],
        "recipient_count": len(email_recipients),
        "line_recipient_count": len(line_recipients),
        "template_subject": template.subject if template else None,
        "already_sent": already_sent,
        "already_sent_email": already_sent_email,
        "already_sent_line": already_sent_line,
        "can_send_email": can_send_email,
        "can_send_line": can_send_line,
        "can_send": can_send,
    }


async def send_cutting_trial_notification(
    db: AsyncSession,
    *,
    production_day: str,
    current_user: User,
) -> dict:
    prod_day = parse_production_day(production_day)
    reference_key = f"{REFERENCE_PREFIX}:{prod_day.isoformat()}"

    setting = await _get_notification_setting(db)
    if not setting or not setting.is_active:
        raise HTTPException(status_code=400, detail="このイベントの通知が無効です")

    email_enabled = bool(setting.email_enabled)
    line_enabled = bool(setting.line_enabled)
    if not email_enabled and not line_enabled:
        raise HTTPException(status_code=400, detail="メール・LINE いずれの通知も有効ではありません")

    rows = await _fetch_trial_rows(db, prod_day)
    if not rows:
        raise HTTPException(
            status_code=400,
            detail="送信対象の試作完了データがありません（備考に「試作」を含み完了済みの行がありません）",
        )

    smtp = await load_smtp_config(db) if email_enabled else None
    line_cfg = await load_line_config(db) if line_enabled else None
    template = await load_email_template(db, EVENT_CODE) if email_enabled else None

    email_recipients = await resolve_notification_recipients(db, EVENT_CODE) if email_enabled else []
    line_recipients = await resolve_line_recipients(db, EVENT_CODE) if line_enabled else []

    can_email = email_enabled and smtp and template and email_recipients
    can_line = line_enabled and line_cfg and line_recipients
    if not can_email and not can_line:
        raise HTTPException(
            status_code=400,
            detail="送信可能なチャネルがありません（SMTP/LINE 設定・受信者・テンプレートを確認してください）",
        )

    sent_at = now_jst()
    sent_at_str = (
        sent_at.strftime("%Y-%m-%d %H:%M")
        if isinstance(sent_at, datetime)
        else str(sent_at)
    )
    variables = _build_variables(
        prod_day=prod_day,
        rows=rows,
        current_user=current_user,
        sent_at_str=sent_at_str,
    )

    email_sent_count = 0
    line_sent_count = 0
    email_failed: list[dict[str, str]] = []
    line_failed: list[dict[str, str]] = []

    if can_email:
        subject = render_template(template.subject, variables)
        body = render_template(template.body, variables)
        for recipient in email_recipients:
            result = await send_html_email(smtp, recipient.email, subject, body)
            log = EmailSendLog(
                event_code=EVENT_CODE,
                reference_key=reference_key,
                recipient_email=recipient.email,
                subject=subject,
                status="success" if result.success else "failed",
                error_message=result.error,
                sent_by_user_id=current_user.id,
            )
            db.add(log)
            if result.success:
                email_sent_count += 1
            else:
                email_failed.append({"email": recipient.email, "error": result.error or "送信失敗"})

    if can_line:
        line_subject = render_template(
            template.subject if template else "【Smart-EMAP】切断試作完了通知 {production_day}",
            variables,
        )
        plain_parts = [
            "切断指示（試作）の完了分をお知らせします。",
            f"対象生産日: {variables['production_day']}",
            f"件数: {variables['item_count']} 件",
            f"生産数合計: {variables['total_quantity']} 本",
        ]
        if variables.get("item_list_text"):
            plain_parts.append(str(variables["item_list_text"]))
        plain_parts.append("Smart-EMAP 生産管理システム")
        line_text = f"{line_subject}\n\n" + "\n".join(plain_parts)

        for recipient in line_recipients:
            result = await push_line_text_message(line_cfg, recipient.line_user_id, line_text)
            preview = line_text[:200]
            log = LineSendLog(
                event_code=EVENT_CODE,
                reference_key=reference_key,
                line_user_id=recipient.line_user_id,
                message_preview=preview,
                status="success" if result.success else "failed",
                error_message=result.error,
                sent_by_user_id=current_user.id,
            )
            db.add(log)
            if result.success:
                line_sent_count += 1
            else:
                line_failed.append(
                    {"line_user_id": recipient.line_user_id, "error": result.error or "送信失敗"}
                )

    await db.commit()

    total_sent = email_sent_count + line_sent_count
    if total_sent == 0:
        err_parts = []
        if email_failed:
            err_parts.append(f"メール: {email_failed[0]['error']}")
        if line_failed:
            err_parts.append(f"LINE: {line_failed[0]['error']}")
        raise HTTPException(
            status_code=500,
            detail="通知送信に失敗しました: " + (" / ".join(err_parts) or "不明"),
        )

    msg_parts = []
    if email_sent_count:
        msg_parts.append(f"メール{email_sent_count}件")
    if line_sent_count:
        msg_parts.append(f"LINE{line_sent_count}件")
    message = "試作完了通知を" + "・".join(msg_parts) + "送信しました"
    if email_failed or line_failed:
        message += f"（一部失敗: メール{len(email_failed)}・LINE{len(line_failed)}）"

    return {
        "success": True,
        "sent_count": total_sent,
        "email_sent_count": email_sent_count,
        "line_sent_count": line_sent_count,
        "failed": email_failed,
        "line_failed": line_failed,
        "message": message,
        "item_count": len(rows),
    }
