"""大量廃棄・保留品 未処理通知メール"""
from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.auth.models import User
from app.modules.erp.bulk_disposal_retention_models import BulkDisposalRetentionRecord
from app.modules.system.settings_models import EmailSendLog, NotificationSetting
from app.services.email_service import (
    load_email_template,
    load_smtp_config,
    render_template,
    send_html_email,
)

EVENT_CODE = "BULK_DISPOSAL_RETENTION_PENDING"
REFERENCE_PREFIX = "bulk_disposal_retention_pending"
SYSTEM_SENDER_LABEL = "Smart-EMAP"


async def _get_notification_setting(db: AsyncSession) -> NotificationSetting | None:
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.event_code == EVENT_CODE)
    )
    return result.scalar_one_or_none()


def _record_to_dict(row: BulkDisposalRetentionRecord) -> dict:
    return {
        "id": row.id,
        "occurred_date": row.occurred_date.isoformat() if row.occurred_date else None,
        "report_category": row.report_category,
        "process_name": row.process_name,
        "product_cd": row.product_cd,
        "product_name": row.product_name,
        "quantity": int(row.quantity or 0),
        "handling_status": row.handling_status,
        "processed_date": row.processed_date.isoformat() if row.processed_date else None,
        "management_no": row.management_no,
        "remarks": row.remarks,
    }


def _build_item_summaries(rows: list[dict]) -> tuple[str, str, int]:
    if not rows:
        return "", "", 0

    html_lines = []
    text_lines = []
    total_qty = 0
    for row in rows:
        occurred = row.get("occurred_date") or "—"
        category = row.get("report_category") or "—"
        process = row.get("process_name") or "—"
        product = (row.get("product_name") or row.get("product_cd") or "—").strip() or "—"
        qty = int(row.get("quantity") or 0)
        mgmt = row.get("management_no") or "—"
        total_qty += qty
        html_lines.append(
            f"<tr><td>{occurred}</td><td>{category}</td><td>{process}</td>"
            f"<td>{product}</td><td align='right'>{qty:,}</td><td>{mgmt}</td></tr>"
        )
        text_lines.append(
            f"  発生日:{occurred}  区分:{category}  工程:{process}  "
            f"製品:{product}  本数:{qty:,}  管理No:{mgmt}"
        )

    item_table = (
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>発生日</th><th>報告区分</th><th>発生工程</th>"
        "<th>製品名</th><th>発生本数</th><th>管理No</th></tr>"
        f"{''.join(html_lines)}</table>"
    )
    item_list_text = "明細:\n" + "\n".join(text_lines)
    return item_table, item_list_text, total_qty


def _build_variables(
    *,
    rows: list[dict],
    sent_at_str: str,
) -> dict:
    item_table, item_list_text, total_qty = _build_item_summaries(rows)
    return {
        "item_count": len(rows),
        "total_quantity": f"{total_qty:,}",
        "item_table": item_table,
        "item_list_text": item_list_text,
        "sent_by": SYSTEM_SENDER_LABEL,
        "sent_at": sent_at_str,
    }


async def _fetch_pending_rows(
    db: AsyncSession,
    *,
    record_ids: list[int] | None = None,
) -> list[dict]:
    query = select(BulkDisposalRetentionRecord).where(
        BulkDisposalRetentionRecord.handling_status == "未処理"
    )
    if record_ids:
        query = query.where(BulkDisposalRetentionRecord.id.in_(record_ids))
    query = query.order_by(
        BulkDisposalRetentionRecord.occurred_date.asc(),
        BulkDisposalRetentionRecord.id.asc(),
    )
    result = await db.execute(query)
    return [_record_to_dict(r) for r in result.scalars().all()]


async def _resolve_user_emails(db: AsyncSession, user_ids: list[int]) -> list[dict]:
    if not user_ids:
        return []
    result = await db.execute(
        select(User).where(User.id.in_(user_ids), User.is_active.is_(True))
    )
    recipients: dict[str, dict] = {}
    for user in result.scalars().all():
        email = (user.email or "").strip()
        if email:
            recipients[email.lower()] = {
                "email": email,
                "name": user.full_name or user.username or email,
                "user_id": user.id,
            }
    return list(recipients.values())


async def get_bulk_disposal_retention_notification_preview(
    db: AsyncSession,
    *,
    record_ids: list[int] | None = None,
) -> dict:
    setting = await _get_notification_setting(db)
    email_enabled = bool(setting and setting.is_active and setting.email_enabled)

    rows = await _fetch_pending_rows(db, record_ids=record_ids)
    _, _, total_qty = _build_item_summaries(rows)
    template = await load_email_template(db, EVENT_CODE)
    smtp = await load_smtp_config(db)

    return {
        "success": True,
        "item_count": len(rows),
        "total_quantity": total_qty,
        "items": rows,
        "email_enabled": email_enabled,
        "smtp_configured": smtp is not None,
        "template_subject": template.subject if template else None,
        "can_send": email_enabled and smtp is not None and template is not None and len(rows) > 0,
    }


async def send_bulk_disposal_retention_notification(
    db: AsyncSession,
    *,
    user_ids: list[int],
    current_user: User,
    record_ids: list[int] | None = None,
) -> dict:
    if not user_ids:
        raise HTTPException(status_code=400, detail="通知先ユーザーを指定してください")

    setting = await _get_notification_setting(db)
    if not setting or not setting.is_active or not setting.email_enabled:
        raise HTTPException(status_code=400, detail="このイベントのメール通知が無効です")

    rows = await _fetch_pending_rows(db, record_ids=record_ids)
    if not rows:
        raise HTTPException(status_code=400, detail="通知対象の未処理データがありません")

    recipients = await _resolve_user_emails(db, user_ids)
    if not recipients:
        raise HTTPException(status_code=400, detail="有効なメールアドレスを持つユーザーが見つかりません")

    smtp = await load_smtp_config(db)
    template = await load_email_template(db, EVENT_CODE)
    if not smtp or not template:
        raise HTTPException(status_code=400, detail="SMTP またはメールテンプレートが未設定です")

    sent_at = now_jst()
    sent_at_str = (
        sent_at.strftime("%Y-%m-%d %H:%M") if isinstance(sent_at, datetime) else str(sent_at)
    )
    variables = _build_variables(rows=rows, sent_at_str=sent_at_str)
    subject = render_template(template.subject, variables)
    body = render_template(template.body, variables)

    reference_key = f"{REFERENCE_PREFIX}:{sent_at_str}:{len(rows)}"
    email_sent_count = 0
    email_failed: list[dict[str, str]] = []

    for recipient in recipients:
        result = await send_html_email(smtp, recipient["email"], subject, body)
        log = EmailSendLog(
            event_code=EVENT_CODE,
            reference_key=reference_key,
            recipient_email=recipient["email"],
            subject=subject,
            status="success" if result.success else "failed",
            error_message=result.error,
            sent_by_user_id=current_user.id,
        )
        db.add(log)
        if result.success:
            email_sent_count += 1
        else:
            email_failed.append({"email": recipient["email"], "error": result.error or "送信失敗"})

    await db.commit()

    return {
        "success": email_sent_count > 0,
        "message": f"{email_sent_count} 件のメールを送信しました"
        + (f"（{len(email_failed)} 件失敗）" if email_failed else ""),
        "item_count": len(rows),
        "total_quantity": variables["total_quantity"],
        "email_sent_count": email_sent_count,
        "email_failed": email_failed,
        "recipient_count": len(recipients),
    }
