"""レポート配信サービス（生成 → 受信者解決 → メール添付/LINE 送信 → 履歴記録）"""
from __future__ import annotations

import asyncio
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.auth.models import User
from app.modules.reports.generators import GeneratedReport, get_generator
from app.modules.reports.models import ReportDefinition, ReportSendLog
from app.modules.system.settings_models import EmailSendLog, LineSendLog, NotificationSetting
from app.services.email_service import (
    DEFAULT_BULK_EMAIL_INTERVAL_SEC,
    EmailAttachment,
    is_smtp_rate_limit_message,
    load_email_template,
    load_smtp_config,
    render_template,
    send_bulk_html_email_with_attachments,
)
from app.services.line_service import load_line_config, push_line_text_message
from app.services.notification_recipient_service import (
    resolve_line_recipients,
    resolve_notification_recipients,
)

SYSTEM_SENDER_LABEL = "Smart-EMAPシステム"
AUTO_SEND_NOTICE = "※ 本メールは Smart-EMAP システムより自動送信されています。"
# SMTP のレート制限（too much mail）回避用：複数宛先の送信間隔（秒）
EMAIL_SEND_INTERVAL_SEC = DEFAULT_BULK_EMAIL_INTERVAL_SEC


async def _get_definition(db: AsyncSession, report_code: str) -> ReportDefinition:
    result = await db.execute(
        select(ReportDefinition).where(ReportDefinition.report_code == report_code)
    )
    definition = result.scalar_one_or_none()
    if not definition or not definition.is_active:
        raise HTTPException(status_code=404, detail="レポート定義が見つからないか無効です")
    return definition


async def _get_notification_setting(db: AsyncSession, event_code: str) -> NotificationSetting | None:
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.event_code == event_code)
    )
    return result.scalar_one_or_none()


def _resolve_format(definition: ReportDefinition, requested: str | None) -> str:
    fmt = (requested or definition.default_format or "xlsx").lower()
    return fmt if fmt in ("xlsx", "pdf", "both") else "xlsx"


async def generate_report(
    db: AsyncSession,
    *,
    report_code: str,
    parameters: dict,
    fmt: str | None = None,
    run_date: date | None = None,
) -> tuple[ReportDefinition, GeneratedReport, str]:
    """レポートを生成して (定義, 生成結果, 形式) を返す。送信は行わない。"""
    definition = await _get_definition(db, report_code)
    generator = get_generator(report_code)
    if generator is None:
        raise HTTPException(status_code=400, detail="このレポートの生成器が未実装です")
    resolved_fmt = _resolve_format(definition, fmt)
    run = run_date or now_jst().date()
    report = await generator.generate(db, parameters=parameters or {}, fmt=resolved_fmt, run_date=run)
    return definition, report, resolved_fmt


async def get_report_preview(
    db: AsyncSession,
    *,
    report_code: str,
    parameters: dict,
) -> dict:
    from app.modules.reports.definition_defaults import CUTTING_REPORT_CODE, ensure_cutting_email_template

    if report_code == CUTTING_REPORT_CODE:
        await ensure_cutting_email_template(db)
    definition, report, resolved_fmt = await generate_report(
        db, report_code=report_code, parameters=parameters
    )
    event_code = definition.event_code
    setting = await _get_notification_setting(db, event_code)
    email_enabled = bool(setting and setting.is_active and setting.email_enabled)
    line_enabled = bool(setting and setting.is_active and setting.line_enabled)

    email_recipients = await resolve_notification_recipients(db, event_code)
    line_recipients = await resolve_line_recipients(db, event_code)
    smtp = await load_smtp_config(db) if email_enabled else None
    line_cfg = await load_line_config(db) if line_enabled else None
    template = await load_email_template(db, event_code)

    can_send_email = bool(email_enabled and smtp and template and email_recipients)
    can_send_line = bool(line_enabled and line_cfg and line_recipients)

    return {
        "success": True,
        "report_code": report_code,
        "report_name": definition.report_name,
        "format": resolved_fmt,
        "period_label": report.period_label,
        "record_count": report.record_count,
        "summary_html": report.summary_html,
        "chart_data": report.extra_variables.get("chart_data"),
        "attachments": [
            {"filename": a.filename, "size": len(a.content)} for a in report.attachments
        ],
        "email_enabled": email_enabled,
        "line_enabled": line_enabled,
        "smtp_configured": smtp is not None,
        "line_configured": line_cfg is not None,
        "template_subject": template.subject if template else None,
        "recipients": [
            {"email": r.email, "name": r.name, "source": r.source} for r in email_recipients
        ],
        "line_recipients": [
            {"line_user_id": r.line_user_id, "name": r.name, "source": r.source}
            for r in line_recipients
        ],
        "recipient_count": len(email_recipients),
        "line_recipient_count": len(line_recipients),
        "can_send_email": can_send_email,
        "can_send_line": can_send_line,
        "can_send": can_send_email or can_send_line,
    }


def _build_variables(definition: ReportDefinition, report: GeneratedReport, *, sent_by: str, sent_at: str) -> dict:
    return {
        "report_name": definition.report_name,
        "period_label": report.period_label,
        "record_count": report.record_count,
        "summary_html": report.summary_html,
        "sent_by": sent_by,
        "sent_at": sent_at,
        **report.extra_variables,
    }


async def send_report(
    db: AsyncSession,
    *,
    report_code: str,
    parameters: dict,
    fmt: str | None = None,
    trigger: str = "manual",
    current_user: User | None = None,
    run_date: date | None = None,
) -> dict:
    is_auto = trigger == "scheduled"
    from app.modules.reports.definition_defaults import CUTTING_REPORT_CODE, ensure_cutting_email_template

    if report_code == CUTTING_REPORT_CODE:
        await ensure_cutting_email_template(db)
    definition, report, resolved_fmt = await generate_report(
        db, report_code=report_code, parameters=parameters, fmt=fmt, run_date=run_date
    )
    event_code = definition.event_code

    setting = await _get_notification_setting(db, event_code)
    if not setting or not setting.is_active:
        if is_auto:
            return {"success": True, "status": "skipped_inactive", "message": "通知イベントが無効です"}
        raise HTTPException(status_code=400, detail="このレポートの通知が無効です")

    email_enabled = bool(setting.email_enabled)
    line_enabled = bool(setting.line_enabled)
    if not email_enabled and not line_enabled:
        if is_auto:
            return {"success": True, "status": "skipped_channels", "message": "メール・LINE が無効です"}
        raise HTTPException(status_code=400, detail="メール・LINE いずれの通知も有効ではありません")

    generator = get_generator(report_code)
    run = run_date or now_jst().date()
    period_key = generator.reference_key(parameters=parameters or {}, run_date=run)
    # 定時配信は実行日（JST）単位で重複判定（手動送信済みでも当日スケジュールは配信可能）
    reference_key = (
        f"{period_key}:scheduled:{run.isoformat()}" if is_auto else period_key
    )

    if is_auto and await _already_sent(db, report_code, reference_key):
        return {
            "success": True,
            "status": "already_sent",
            "reference_key": reference_key,
            "message": "本日の定時配信は送信済みです",
        }

    smtp = await load_smtp_config(db) if email_enabled else None
    line_cfg = await load_line_config(db) if line_enabled else None
    template = await load_email_template(db, event_code) if email_enabled else None

    email_recipients = await resolve_notification_recipients(db, event_code) if email_enabled else []
    line_recipients = await resolve_line_recipients(db, event_code) if line_enabled else []

    can_email = bool(email_enabled and smtp and template and email_recipients)
    can_line = bool(line_enabled and line_cfg and line_recipients)
    if not can_email and not can_line:
        if is_auto:
            return {"success": True, "status": "no_recipients", "message": "送信可能なチャネル・受信者がありません"}
        raise HTTPException(
            status_code=400,
            detail="送信可能なチャネルがありません（SMTP/LINE 設定・受信者・テンプレートを確認してください）",
        )

    sent_at_dt = now_jst()
    sent_at_str = sent_at_dt.strftime("%Y-%m-%d %H:%M") if isinstance(sent_at_dt, datetime) else str(sent_at_dt)
    sent_by = SYSTEM_SENDER_LABEL
    sent_by_user_id = current_user.id if current_user is not None else None
    variables = _build_variables(definition, report, sent_by=sent_by, sent_at=sent_at_str)

    attachments = [
        EmailAttachment(filename=a.filename, content=a.content, mime_type=a.mime_type)
        for a in report.attachments
    ]

    email_sent_count = 0
    line_sent_count = 0
    email_failed: list[dict[str, str]] = []
    line_failed: list[dict[str, str]] = []

    if can_email:
        subject = render_template(template.subject, variables)
        body = render_template(template.body, variables)
        deliveries = [(recipient.email, subject, body) for recipient in email_recipients]
        email_results = await send_bulk_html_email_with_attachments(
            smtp,
            deliveries,
            attachments,
            interval_sec=EMAIL_SEND_INTERVAL_SEC,
        )
        for recipient, result in zip(email_recipients, email_results, strict=False):
            db.add(
                EmailSendLog(
                    event_code=event_code,
                    reference_key=reference_key,
                    recipient_email=recipient.email,
                    subject=subject,
                    status="success" if result.success else "failed",
                    error_message=result.error,
                    sent_by_user_id=sent_by_user_id,
                )
            )
            if result.success:
                email_sent_count += 1
            else:
                email_failed.append({"email": recipient.email, "error": result.error or "送信失敗"})

    if can_line:
        line_subject = render_template(template.subject if template else definition.report_name, variables)
        line_text = "\n\n".join(
            [
                line_subject,
                report.summary_text,
                AUTO_SEND_NOTICE,
                f"送信者: {sent_by} / 送信日時: {sent_at_str}",
            ]
        )
        for recipient in line_recipients:
            result = await push_line_text_message(line_cfg, recipient.line_user_id, line_text)
            db.add(
                LineSendLog(
                    event_code=event_code,
                    reference_key=reference_key,
                    line_user_id=recipient.line_user_id,
                    message_preview=line_text[:200],
                    status="success" if result.success else "failed",
                    error_message=result.error,
                    sent_by_user_id=sent_by_user_id,
                )
            )
            if result.success:
                line_sent_count += 1
            else:
                line_failed.append({"line_user_id": recipient.line_user_id, "error": result.error or "送信失敗"})

    total_sent = email_sent_count + line_sent_count
    recipient_count = len(email_recipients) + len(line_recipients)
    has_failures = bool(email_failed or line_failed)
    status = "success" if total_sent and not has_failures else ("partial" if total_sent else "failed")
    message = _build_message(email_sent_count, line_sent_count, email_failed, line_failed)
    first_attachment = report.attachments[0] if report.attachments else None

    db.add(
        ReportSendLog(
            report_code=report_code,
            trigger_type=trigger,
            reference_key=reference_key,
            parameters=parameters or {},
            file_name=first_attachment.filename if first_attachment else None,
            file_size=len(first_attachment.content) if first_attachment else None,
            recipient_count=recipient_count,
            success_count=total_sent,
            status=status,
            message=message,
            error_message=None if not has_failures else _first_error(email_failed, line_failed),
            triggered_by=sent_by_user_id,
        )
    )
    await db.commit()

    if total_sent == 0 and not is_auto:
        detail = "レポート送信に失敗しました: " + message
        if any(is_smtp_rate_limit_message(err.get("error", "")) for err in email_failed):
            detail += "（メールサーバーの送信制限です。数分待ってから再送してください）"
        raise HTTPException(status_code=503, detail=detail)

    return {
        "success": True,
        "status": status,
        "trigger": trigger,
        "report_code": report_code,
        "period_label": report.period_label,
        "reference_key": reference_key,
        "email_sent_count": email_sent_count,
        "line_sent_count": line_sent_count,
        "total_sent": total_sent,
        "email_failed": email_failed,
        "line_failed": line_failed,
        "message": message,
    }


async def _already_sent(db: AsyncSession, report_code: str, reference_key: str) -> bool:
    result = await db.execute(
        select(ReportSendLog.id).where(
            ReportSendLog.report_code == report_code,
            ReportSendLog.reference_key == reference_key,
            ReportSendLog.status.in_(["success", "partial"]),
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


def _first_error(email_failed: list[dict], line_failed: list[dict]) -> str:
    if email_failed:
        return f"メール: {email_failed[0]['error']}"
    if line_failed:
        return f"LINE: {line_failed[0]['error']}"
    return ""


def _build_message(
    email_sent: int, line_sent: int, email_failed: list[dict], line_failed: list[dict]
) -> str:
    parts: list[str] = []
    if email_sent:
        parts.append(f"メール{email_sent}件")
    if line_sent:
        parts.append(f"LINE{line_sent}件")
    if not parts:
        if email_failed or line_failed:
            return _first_error(email_failed, line_failed)
        return "送信対象がありません"
    msg = "・".join(parts) + "を送信しました"
    if email_failed or line_failed:
        msg += f"（一部失敗: メール{len(email_failed)}・LINE{len(line_failed)}）"
    return msg
