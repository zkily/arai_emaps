"""実績確定通知送信（メール + LINE・切断・面取共通）"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.auth.models import User
from app.modules.system.settings_models import EmailSendLog, LineSendLog, NotificationSetting
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

CUTTING_EVENT = "CUTTING_ACTUAL_CONFIRMED"
CHAMFERING_EVENT = "CHAMFERING_ACTUAL_CONFIRMED"

_PROCESS_META = {
    "cutting": {
        "event_code": CUTTING_EVENT,
        "source_file": "cutting_management",
        "process_label": "切断",
        "reference_prefix": "cutting",
    },
    "chamfering": {
        "event_code": CHAMFERING_EVENT,
        "source_file": "chamfering_management",
        "process_label": "面取",
        "reference_prefix": "chamfering",
    },
}


def parse_production_day(production_day: str) -> date:
    try:
        parts = production_day.strip().split("-")
        if len(parts) != 3:
            raise ValueError("invalid")
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=400, detail="production_day の形式が不正です") from exc


async def _get_notification_setting(db: AsyncSession, event_code: str) -> NotificationSetting | None:
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.event_code == event_code)
    )
    return result.scalar_one_or_none()


async def _aggregate_actual_stats(
    db: AsyncSession,
    *,
    source_file: str,
    prod_day: date,
) -> tuple[int, int, str, str]:
    """登録件数、数量合計、設備別 HTML / テキストサマリー。"""
    stats_sql = text("""
        SELECT
            COUNT(*) AS inserted_count,
            COALESCE(SUM(quantity), 0) AS total_quantity
        FROM stock_transaction_logs
        WHERE source_file = :source_file
          AND DATE(transaction_time) = :production_day
          AND transaction_type = '実績'
    """)
    stats_res = await db.execute(
        stats_sql, {"source_file": source_file, "production_day": prod_day}
    )
    stats = stats_res.mappings().first() or {}
    inserted_count = int(stats.get("inserted_count") or 0)
    total_quantity = int(stats.get("total_quantity") or 0)

    machine_sql = text("""
        SELECT machine_cd, COALESCE(SUM(quantity), 0) AS qty
        FROM stock_transaction_logs
        WHERE source_file = :source_file
          AND DATE(transaction_time) = :production_day
          AND transaction_type = '実績'
        GROUP BY machine_cd
        ORDER BY machine_cd
    """)
    machine_res = await db.execute(
        machine_sql, {"source_file": source_file, "production_day": prod_day}
    )
    machine_rows = machine_res.mappings().fetchall()
    if not machine_rows:
        return inserted_count, total_quantity, "", ""

    html_lines = "".join(
        f"<tr><td>{r.get('machine_cd') or '—'}</td><td align='right'>{int(r.get('qty') or 0):,} 本</td></tr>"
        for r in machine_rows
    )
    machine_summary_html = (
        "<p>設備別内訳:</p><table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>設備</th><th>数量</th></tr>"
        f"{html_lines}</table>"
    )
    text_lines = "\n".join(
        f"  {(r.get('machine_cd') or '—')}: {int(r.get('qty') or 0):,} 本" for r in machine_rows
    )
    machine_summary_text = f"設備別内訳:\n{text_lines}"
    return inserted_count, total_quantity, machine_summary_html, machine_summary_text


def _build_variables(
    *,
    meta: dict,
    prod_day: date,
    inserted_count: int,
    total_quantity: int,
    machine_summary_html: str,
    machine_summary_text: str,
    current_user: User,
    confirmed_at_str: str,
) -> dict:
    return {
        "production_day": prod_day.isoformat(),
        "inserted_count": inserted_count,
        "total_quantity": f"{total_quantity:,}",
        "confirmed_by": (current_user.full_name or current_user.username or ""),
        "confirmed_at": confirmed_at_str,
        "machine_summary": machine_summary_html,
        "machine_summary_text": machine_summary_text,
        "process_label": meta["process_label"],
    }


async def _already_sent_email(db: AsyncSession, event_code: str, reference_key: str) -> bool:
    log_res = await db.execute(
        select(EmailSendLog).where(
            EmailSendLog.event_code == event_code,
            EmailSendLog.reference_key == reference_key,
            EmailSendLog.status == "success",
        )
    )
    return log_res.scalars().first() is not None


async def _already_sent_line(db: AsyncSession, event_code: str, reference_key: str) -> bool:
    log_res = await db.execute(
        select(LineSendLog).where(
            LineSendLog.event_code == event_code,
            LineSendLog.reference_key == reference_key,
            LineSendLog.status == "success",
        )
    )
    return log_res.scalars().first() is not None


async def get_confirm_actual_email_preview(
    db: AsyncSession,
    *,
    process_type: str,
    production_day: str,
) -> dict:
    meta = _PROCESS_META.get(process_type)
    if not meta:
        raise HTTPException(status_code=400, detail="process_type が不正です")

    prod_day = parse_production_day(production_day)
    event_code = meta["event_code"]
    reference_key = f"{meta['reference_prefix']}:{prod_day.isoformat()}"

    setting = await _get_notification_setting(db, event_code)
    email_enabled = bool(setting and setting.is_active and setting.email_enabled)
    line_enabled = bool(setting and setting.is_active and setting.line_enabled)

    email_recipients = await resolve_notification_recipients(db, event_code)
    line_recipients = await resolve_line_recipients(db, event_code)
    inserted_count, total_quantity, _, _ = await _aggregate_actual_stats(
        db, source_file=meta["source_file"], prod_day=prod_day
    )

    template = await load_email_template(db, event_code)
    smtp = await load_smtp_config(db)
    line_cfg = await load_line_config(db)

    already_sent_email = await _already_sent_email(db, event_code, reference_key)
    already_sent_line = await _already_sent_line(db, event_code, reference_key)

    can_send_email = email_enabled and smtp is not None and len(email_recipients) > 0 and inserted_count > 0
    can_send_line = line_enabled and line_cfg is not None and len(line_recipients) > 0 and inserted_count > 0
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

    return {
        "success": True,
        "process_type": process_type,
        "process_label": meta["process_label"],
        "production_day": prod_day.isoformat(),
        "email_enabled": email_enabled,
        "line_enabled": line_enabled,
        "smtp_configured": smtp is not None,
        "line_configured": line_cfg is not None,
        "inserted_count": inserted_count,
        "total_quantity": total_quantity,
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


async def send_confirm_actual_email(
    db: AsyncSession,
    *,
    process_type: str,
    production_day: str,
    current_user: User,
) -> dict:
    meta = _PROCESS_META.get(process_type)
    if not meta:
        raise HTTPException(status_code=400, detail="process_type が不正です")

    prod_day = parse_production_day(production_day)
    event_code = meta["event_code"]
    reference_key = f"{meta['reference_prefix']}:{prod_day.isoformat()}"

    setting = await _get_notification_setting(db, event_code)
    if not setting or not setting.is_active:
        raise HTTPException(status_code=400, detail="このイベントの通知が無効です")

    email_enabled = bool(setting.email_enabled)
    line_enabled = bool(setting.line_enabled)
    if not email_enabled and not line_enabled:
        raise HTTPException(status_code=400, detail="メール・LINE いずれの通知も有効ではありません")

    smtp = await load_smtp_config(db) if email_enabled else None
    line_cfg = await load_line_config(db) if line_enabled else None
    template = await load_email_template(db, event_code) if email_enabled else None

    email_recipients = await resolve_notification_recipients(db, event_code) if email_enabled else []
    line_recipients = await resolve_line_recipients(db, event_code) if line_enabled else []

    can_email = email_enabled and smtp and template and email_recipients
    can_line = line_enabled and line_cfg and line_recipients
    if not can_email and not can_line:
        raise HTTPException(
            status_code=400,
            detail="送信可能なチャネルがありません（SMTP/LINE 設定・受信者・テンプレートを確認してください）",
        )

    inserted_count, total_quantity, machine_summary_html, machine_summary_text = await _aggregate_actual_stats(
        db, source_file=meta["source_file"], prod_day=prod_day
    )
    if inserted_count <= 0:
        raise HTTPException(status_code=400, detail="送信対象の実績データがありません")

    confirmed_at = now_jst()
    confirmed_at_str = (
        confirmed_at.strftime("%Y-%m-%d %H:%M")
        if isinstance(confirmed_at, datetime)
        else str(confirmed_at)
    )
    variables = _build_variables(
        meta=meta,
        prod_day=prod_day,
        inserted_count=inserted_count,
        total_quantity=total_quantity,
        machine_summary_html=machine_summary_html,
        machine_summary_text=machine_summary_text,
        current_user=current_user,
        confirmed_at_str=confirmed_at_str,
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
                event_code=event_code,
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
            template.subject if template else "【Smart-EMAP】{process_label}実績確定 {production_day}",
            variables,
        )
        plain_parts = [
            f"{meta['process_label']}実績が確定されました。",
            f"生産日: {variables['production_day']}",
            f"登録件数: {variables['inserted_count']} 件",
            f"数量合計: {variables['total_quantity']} 本",
            f"確定者: {variables['confirmed_by']}",
            f"確定日時: {variables['confirmed_at']}",
        ]
        if machine_summary_text:
            plain_parts.append(machine_summary_text)
        plain_parts.append("Smart-EMAP 生産管理システム")
        line_text = f"{line_subject}\n\n" + "\n".join(plain_parts)

        for recipient in line_recipients:
            result = await push_line_text_message(line_cfg, recipient.line_user_id, line_text)
            preview = line_text[:200]
            log = LineSendLog(
                event_code=event_code,
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
    message = "・".join(msg_parts) + "を送信しました"
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
    }
