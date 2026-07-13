"""製品用ラベル 外注注文メール通知"""
from __future__ import annotations

import base64
import html
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.auth.models import User
from app.modules.master.models import Product, ProductUseLabelConfig
from app.modules.master.product_label_service import SUPPLY_TYPE_OUTSOURCE
from app.modules.master.product_use_label_service import config_to_dict
from app.modules.system.settings_models import EmailSendLog, NotificationSetting
from app.services.email_service import (
    EmailAttachment,
    EmailSendResult,
    load_email_template,
    load_smtp_config,
    render_template,
    send_html_email_with_attachments,
)

EVENT_CODE = "PRODUCT_USE_LABEL_OUTSOURCE_ORDER"
REFERENCE_PREFIX = "product_use_label_outsource_order"
_PRODUCT_CD_COLLATION = "utf8mb4_unicode_ci"


def _product_cd_join():
    return ProductUseLabelConfig.product_cd.collate(_PRODUCT_CD_COLLATION) == Product.product_cd.collate(
        _PRODUCT_CD_COLLATION
    )


async def _get_notification_setting(db: AsyncSession) -> NotificationSetting | None:
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.event_code == EVENT_CODE)
    )
    return result.scalar_one_or_none()


async def fetch_outsource_use_label_configs(db: AsyncSession) -> list[dict]:
    query = (
        select(ProductUseLabelConfig, Product.product_name, Product.status)
        .outerjoin(Product, _product_cd_join())
        .where(ProductUseLabelConfig.supply_type == SUPPLY_TYPE_OUTSOURCE)
        .order_by(Product.product_name.asc(), ProductUseLabelConfig.product_cd.asc())
    )
    result = await db.execute(query)
    rows = result.all()
    items: list[dict] = []
    for config, master_name, product_status in rows:
        items.append(
            config_to_dict(
                config,
                master_product_name=master_name or "",
                product_status=product_status,
            )
        )
    return items


def _build_item_table_html(items: list[dict]) -> str:
    lines = [
        "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;font-size:13px'>",
        "<thead><tr>"
        "<th>製品CD</th><th>製品用製品名</th><th>入数</th><th>用紙色</th><th>注文数</th>"
        "</tr></thead><tbody>",
    ]
    for row in items:
        qty = row.get("unit_qty")
        qty_text = "" if qty is None else str(qty)
        lines.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('product_cd') or ''))}</td>"
            f"<td>{html.escape(str(row.get('use_label_product_name') or row.get('master_product_name') or ''))}</td>"
            f"<td align='right'>{html.escape(qty_text)}</td>"
            f"<td>{html.escape(str(row.get('paper_color') or '白'))}</td>"
            f"<td align='right'><strong>{int(row.get('order_qty') or 0)}</strong></td>"
            "</tr>"
        )
    lines.append("</tbody></table>")
    return "".join(lines)


def _build_item_list_text(items: list[dict]) -> str:
    parts: list[str] = []
    for row in items:
        name = row.get("use_label_product_name") or row.get("master_product_name") or ""
        parts.append(
            f"- {row.get('product_cd')} / {name} / 入数:{row.get('unit_qty') or '—'} "
            f"/ 用紙:{row.get('paper_color') or '白'} / 注文数:{int(row.get('order_qty') or 0)}"
        )
    return "\n".join(parts)


async def _resolve_user_emails(db: AsyncSession, user_ids: list[int]) -> list[dict]:
    if not user_ids:
        return []
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
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


def _decode_attachments(payloads: list[dict]) -> list[EmailAttachment]:
    attachments: list[EmailAttachment] = []
    for item in payloads:
        filename = (item.get("filename") or "").strip()
        content_b64 = (item.get("content_base64") or "").strip()
        if not filename or not content_b64:
            continue
        try:
            content = base64.b64decode(content_b64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"添付ファイルの形式が不正です: {filename}") from exc
        mime_type = (item.get("mime_type") or "application/pdf").strip() or "application/pdf"
        attachments.append(EmailAttachment(filename=filename, content=content, mime_type=mime_type))
    return attachments


async def get_outsource_order_email_preview(db: AsyncSession) -> dict:
    setting = await _get_notification_setting(db)
    email_enabled = bool(setting and setting.is_active and setting.email_enabled)
    items = await fetch_outsource_use_label_configs(db)
    template = await load_email_template(db, EVENT_CODE)
    smtp = await load_smtp_config(db)
    return {
        "success": True,
        "item_count": len(items),
        "items": items,
        "email_enabled": email_enabled,
        "smtp_configured": smtp is not None,
        "template_subject": template.subject if template else None,
        "can_send": email_enabled and smtp is not None and template is not None,
    }


async def send_outsource_order_email(
    db: AsyncSession,
    *,
    user_ids: list[int],
    items: list[dict],
    attachments_payload: list[dict],
    current_user: User,
) -> dict:
    if not user_ids:
        raise HTTPException(status_code=400, detail="通知先ユーザーを指定してください")

    order_items = [row for row in items if int(row.get("order_qty") or 0) > 0]
    if not order_items:
        raise HTTPException(status_code=400, detail="注文数が1以上の行がありません")

    setting = await _get_notification_setting(db)
    if not setting or not setting.is_active or not setting.email_enabled:
        raise HTTPException(status_code=400, detail="このイベントのメール通知が無効です")

    recipients = await _resolve_user_emails(db, user_ids)
    if not recipients:
        raise HTTPException(status_code=400, detail="有効なメールアドレスを持つユーザーが見つかりません")

    smtp = await load_smtp_config(db)
    template = await load_email_template(db, EVENT_CODE)
    if not smtp or not template:
        raise HTTPException(status_code=400, detail="SMTP またはメールテンプレートが未設定です")

    attachments = _decode_attachments(attachments_payload)
    if not attachments:
        raise HTTPException(status_code=400, detail="ラベル添付ファイルがありません")

    sent_at = now_jst()
    sent_at_str = sent_at.strftime("%Y-%m-%d %H:%M") if isinstance(sent_at, datetime) else str(sent_at)
    total_order_qty = sum(int(row.get("order_qty") or 0) for row in order_items)
    attachment_names = ", ".join(att.filename for att in attachments)
    variables = {
        "item_count": str(len(order_items)),
        "total_order_qty": str(total_order_qty),
        "item_table": _build_item_table_html(order_items),
        "item_list_text": _build_item_list_text(order_items),
        "attachment_count": str(len(attachments)),
        "attachment_names": attachment_names,
        "sent_by": current_user.full_name or current_user.username or "",
        "sent_at": sent_at_str,
    }
    subject = render_template(template.subject, variables)
    body = render_template(template.body, variables)

    reference_key = f"{REFERENCE_PREFIX}:{sent_at_str}:{len(order_items)}"
    email_sent_count = 0
    email_failed: list[dict[str, str]] = []

    for recipient in recipients:
        result: EmailSendResult = await send_html_email_with_attachments(
            smtp, recipient["email"], subject, body, attachments
        )
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
        "item_count": len(order_items),
        "total_order_qty": total_order_qty,
        "attachment_count": len(attachments),
        "email_sent_count": email_sent_count,
        "email_failed": email_failed,
        "recipient_count": len(recipients),
    }
