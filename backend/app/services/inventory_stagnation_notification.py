"""在庫停滞アラート通知（工程別メール・LINE 扇出）"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
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
from app.services.inventory_stagnation_service import (
    fetch_inventory_stagnation_hits,
    inventory_column_label,
)
from app.services.line_service import load_line_config, push_line_text_message
from app.services.notification_recipient_service import (
    resolve_line_recipients,
    resolve_notification_recipients,
)

EVENT_CODE = "INVENTORY_STAGNATION"
REFERENCE_PREFIX = "inventory_stagnation"
SYSTEM_SENDER_LABEL = "Smart-EMAPシステム"
# SMTP サーバーのレート制限（too much mail）回避用
EMAIL_SEND_INTERVAL_SEC = 0.8


async def _get_notification_setting(db: AsyncSession) -> NotificationSetting | None:
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.event_code == EVENT_CODE)
    )
    return result.scalar_one_or_none()


def _reference_key(
    *,
    as_of: str,
    min_quantity: int,
    stable_calendar_days: int,
    inventory_column: str,
) -> str:
    return f"{REFERENCE_PREFIX}:{as_of}:{stable_calendar_days}:{min_quantity}:{inventory_column}"


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


def _build_item_summaries(rows: list[dict]) -> tuple[str, str]:
    if not rows:
        return "", ""
    html_lines = []
    text_lines = []
    for row in rows:
        name = (row.get("product_name") or row.get("product_cd") or "—").strip() or "—"
        qty = int(row.get("stable_quantity") or 0)
        period = f"{row.get('period_start', '')} ～ {row.get('period_end', '')}"
        html_lines.append(
            f"<tr><td>{name}</td><td align='right'>{qty:,}</td><td>{period}</td></tr>"
        )
        text_lines.append(f"  {name}  在庫: {qty:,}  {period}")
    item_table = (
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>製品名</th><th>在庫数</th><th>期間</th></tr>"
        f"{''.join(html_lines)}</table>"
    )
    item_list_text = "明細:\n" + "\n".join(text_lines)
    return item_table, item_list_text


def _build_variables(
    *,
    process_label: str,
    as_of: str,
    min_quantity: int,
    stable_calendar_days: int,
    rows: list[dict],
    sent_by: str,
    sent_at_str: str,
) -> dict:
    item_table, item_list_text = _build_item_summaries(rows)
    return {
        "process_label": process_label,
        "as_of": as_of,
        "min_quantity": str(min_quantity),
        "stable_calendar_days": str(stable_calendar_days),
        "item_count": len(rows),
        "item_table": item_table,
        "item_list_text": item_list_text,
        "sent_by": sent_by,
        "sent_at": sent_at_str,
    }


def _resolve_sender(current_user: User | None) -> tuple[str, int | None]:
    user_id = current_user.id if current_user is not None else None
    return SYSTEM_SENDER_LABEL, user_id


def _friendly_delivery_error(failed: list[dict[str, str]], *, channel: str) -> str:
    for item in failed:
        err = (item.get("error") or "").lower()
        if "too much mail" in err or "4.7.1" in err:
            return (
                f"{channel}サーバーが送信頻度を制限しています（too much mail）。"
                "数分待ってから再試行するか、工程を分けて送信してください。"
            )
    if not failed:
        return "送信失敗"
    first = failed[0].get("error") or "送信失敗"
    return f"{channel}: {first}"


def _build_send_result_message(
    *,
    email_sent_count: int,
    line_sent_count: int,
    email_failed: list[dict[str, str]],
    line_failed: list[dict[str, str]],
) -> str:
    parts: list[str] = []
    if email_sent_count:
        parts.append(f"メール {email_sent_count} 件")
    if line_sent_count:
        parts.append(f"LINE {line_sent_count} 件")
    if not parts:
        hints: list[str] = []
        if email_failed:
            hints.append(_friendly_delivery_error(email_failed, channel="メール"))
        if line_failed:
            hints.append(_friendly_delivery_error(line_failed, channel="LINE"))
        return " / ".join(hints) if hints else "送信に失敗しました"
    msg = "・".join(parts) + "を送信しました"
    if email_failed or line_failed:
        msg += f"（一部失敗: メール {len(email_failed)} / LINE {len(line_failed)}）"
    return msg


def _group_hits_by_column(hits: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in hits:
        grouped[row["inventory_column"]].append(row)
    return dict(grouped)


async def _build_group_preview(
    db: AsyncSession,
    *,
    inventory_column: str,
    rows: list[dict],
    as_of: str,
    min_quantity: int,
    stable_calendar_days: int,
    email_enabled: bool,
    line_enabled: bool,
    smtp_ok: bool,
    line_ok: bool,
) -> dict:
    process_label = inventory_column_label(inventory_column)
    reference_key = _reference_key(
        as_of=as_of,
        min_quantity=min_quantity,
        stable_calendar_days=stable_calendar_days,
        inventory_column=inventory_column,
    )
    email_recipients = await resolve_notification_recipients(
        db, EVENT_CODE, inventory_column=inventory_column
    )
    line_recipients = await resolve_line_recipients(
        db, EVENT_CODE, inventory_column=inventory_column
    )
    item_count = len(rows)
    already_sent_email = await _already_sent_email(db, reference_key)
    already_sent_line = await _already_sent_line(db, reference_key)

    can_send_email = (
        email_enabled and smtp_ok and len(email_recipients) > 0 and item_count > 0 and not already_sent_email
    )
    can_send_line = (
        line_enabled and line_ok and len(line_recipients) > 0 and item_count > 0 and not already_sent_line
    )
    can_send = can_send_email or can_send_line

    already_sent = False
    if email_enabled and line_enabled:
        already_sent = (
            (not email_enabled or not smtp_ok or not email_recipients or already_sent_email)
            and (not line_enabled or not line_ok or not line_recipients or already_sent_line)
            and (already_sent_email or already_sent_line)
            and item_count > 0
        )
    elif email_enabled:
        already_sent = already_sent_email and item_count > 0
    elif line_enabled:
        already_sent = already_sent_line and item_count > 0

    no_recipients = item_count > 0 and not email_recipients and not line_recipients

    return {
        "inventory_column": inventory_column,
        "process_label": process_label,
        "item_count": item_count,
        "reference_key": reference_key,
        "items": [
            {
                "product_cd": r.get("product_cd", ""),
                "product_name": r.get("product_name", ""),
                "stable_quantity": int(r.get("stable_quantity") or 0),
                "period_start": r.get("period_start", ""),
                "period_end": r.get("period_end", ""),
            }
            for r in rows
        ],
        "recipients": [
            {"email": r.email, "name": r.name, "source": r.source} for r in email_recipients
        ],
        "line_recipients": [
            {"line_user_id": r.line_user_id, "name": r.name, "source": r.source}
            for r in line_recipients
        ],
        "recipient_count": len(email_recipients),
        "line_recipient_count": len(line_recipients),
        "already_sent": already_sent,
        "already_sent_email": already_sent_email,
        "already_sent_line": already_sent_line,
        "can_send_email": can_send_email,
        "can_send_line": can_send_line,
        "can_send": can_send,
        "no_recipients": no_recipients,
    }


async def get_inventory_stagnation_notification_preview(
    db: AsyncSession,
    *,
    as_of: str | None = None,
    min_quantity: int = 50,
    stable_calendar_days: int = 7,
) -> dict:
    meta = await fetch_inventory_stagnation_hits(
        db,
        as_of=as_of,
        min_quantity=min_quantity,
        stable_calendar_days=stable_calendar_days,
    )
    setting = await _get_notification_setting(db)
    email_enabled = bool(setting and setting.is_active and setting.email_enabled)
    line_enabled = bool(setting and setting.is_active and setting.line_enabled)

    smtp = await load_smtp_config(db) if email_enabled else None
    line_cfg = await load_line_config(db) if line_enabled else None
    template = await load_email_template(db, EVENT_CODE) if email_enabled else None

    grouped = _group_hits_by_column(meta["list"])
    groups: list[dict] = []
    for col in sorted(grouped.keys(), key=lambda c: inventory_column_label(c)):
        groups.append(
            await _build_group_preview(
                db,
                inventory_column=col,
                rows=grouped[col],
                as_of=meta["as_of"],
                min_quantity=meta["min_quantity"],
                stable_calendar_days=meta["stable_calendar_days"],
                email_enabled=email_enabled,
                line_enabled=line_enabled,
                smtp_ok=smtp is not None,
                line_ok=line_cfg is not None,
            )
        )

    sendable_groups = [g for g in groups if g["can_send"]]
    return {
        "success": True,
        "as_of": meta["as_of"],
        "period_start": meta["period_start"],
        "period_end": meta["period_end"],
        "min_quantity": meta["min_quantity"],
        "stable_calendar_days": meta["stable_calendar_days"],
        "total_count": meta["total"],
        "email_enabled": email_enabled,
        "line_enabled": line_enabled,
        "smtp_configured": smtp is not None,
        "line_configured": line_cfg is not None,
        "template_subject": template.subject if template else None,
        "groups": groups,
        "sendable_group_count": len(sendable_groups),
        "can_send": len(sendable_groups) > 0,
    }


async def send_inventory_stagnation_notification(
    db: AsyncSession,
    *,
    as_of: str | None = None,
    min_quantity: int = 50,
    stable_calendar_days: int = 7,
    inventory_columns: list[str] | None = None,
    current_user: User | None = None,
    trigger: str = "manual",
) -> dict:
    is_auto = trigger == "auto"
    setting = await _get_notification_setting(db)
    if not setting or not setting.is_active:
        if is_auto:
            return {"success": True, "status": "skipped_inactive", "message": "通知イベントが無効です"}
        raise HTTPException(status_code=400, detail="このイベントの通知が無効です")

    email_enabled = bool(setting.email_enabled)
    line_enabled = bool(setting.line_enabled)
    if not email_enabled and not line_enabled:
        if is_auto:
            return {"success": True, "status": "skipped_channels", "message": "メール・LINE が無効です"}
        raise HTTPException(status_code=400, detail="メール・LINE いずれの通知も有効ではありません")

    meta = await fetch_inventory_stagnation_hits(
        db,
        as_of=as_of,
        min_quantity=min_quantity,
        stable_calendar_days=stable_calendar_days,
    )
    if not meta["list"]:
        if is_auto:
            return {
                "success": True,
                "status": "no_hits",
                "as_of": meta["as_of"],
                "total_sent": 0,
                "message": "停滞在庫なし",
            }
        raise HTTPException(status_code=400, detail="送信対象の停滞在庫がありません")

    grouped = _group_hits_by_column(meta["list"])
    target_columns = set(inventory_columns or grouped.keys())
    if inventory_columns:
        unknown = target_columns - set(grouped.keys())
        if unknown:
            raise HTTPException(status_code=400, detail="指定した工程に停滞データがありません")

    smtp = await load_smtp_config(db) if email_enabled else None
    line_cfg = await load_line_config(db) if line_enabled else None
    template = await load_email_template(db, EVENT_CODE) if email_enabled else None

    sent_at = now_jst()
    sent_at_str = (
        sent_at.strftime("%Y-%m-%d %H:%M") if isinstance(sent_at, datetime) else str(sent_at)
    )
    sent_by, sent_by_user_id = _resolve_sender(current_user)

    email_sent_count = 0
    line_sent_count = 0
    email_failed: list[dict[str, str]] = []
    line_failed: list[dict[str, str]] = []
    groups_sent: list[str] = []
    groups_skipped: list[dict[str, str]] = []
    email_dispatch_count = 0

    for col in sorted(target_columns, key=lambda c: inventory_column_label(c)):
        rows = grouped.get(col, [])
        if not rows:
            continue

        process_label = inventory_column_label(col)
        reference_key = _reference_key(
            as_of=meta["as_of"],
            min_quantity=meta["min_quantity"],
            stable_calendar_days=meta["stable_calendar_days"],
            inventory_column=col,
        )

        email_recipients = (
            await resolve_notification_recipients(db, EVENT_CODE, inventory_column=col)
            if email_enabled
            else []
        )
        line_recipients = (
            await resolve_line_recipients(db, EVENT_CODE, inventory_column=col) if line_enabled else []
        )

        can_email = email_enabled and smtp and template and email_recipients
        can_line = line_enabled and line_cfg and line_recipients
        if not can_email and not can_line:
            groups_skipped.append(
                {
                    "inventory_column": col,
                    "process_label": process_label,
                    "reason": "受信者未設定またはチャネル未構成",
                }
            )
            continue

        already_email = await _already_sent_email(db, reference_key) if can_email else False
        already_line = await _already_sent_line(db, reference_key) if can_line else False
        if (can_email and already_email) and (can_line and already_line):
            groups_skipped.append(
                {"inventory_column": col, "process_label": process_label, "reason": "送信済み"}
            )
            continue
        if can_email and already_email:
            can_email = False
        if can_line and already_line:
            can_line = False
        if not can_email and not can_line:
            groups_skipped.append(
                {"inventory_column": col, "process_label": process_label, "reason": "送信済み"}
            )
            continue

        variables = _build_variables(
            process_label=process_label,
            as_of=meta["as_of"],
            min_quantity=meta["min_quantity"],
            stable_calendar_days=meta["stable_calendar_days"],
            rows=rows,
            sent_by=sent_by,
            sent_at_str=sent_at_str,
        )

        group_sent = False
        if can_email:
            subject = render_template(template.subject, variables)
            body = render_template(template.body, variables)
            for recipient in email_recipients:
                if email_dispatch_count > 0:
                    await asyncio.sleep(EMAIL_SEND_INTERVAL_SEC)
                email_dispatch_count += 1
                result = await send_html_email(smtp, recipient.email, subject, body)
                log = EmailSendLog(
                    event_code=EVENT_CODE,
                    reference_key=reference_key,
                    recipient_email=recipient.email,
                    subject=subject,
                    status="success" if result.success else "failed",
                    error_message=result.error,
                    sent_by_user_id=sent_by_user_id,
                )
                db.add(log)
                if result.success:
                    email_sent_count += 1
                    group_sent = True
                else:
                    email_failed.append({"email": recipient.email, "error": result.error or "送信失敗"})

        if can_line:
            line_subject = render_template(
                template.subject if template else "【Smart-EMAP】{process_label} 在庫停滞 {as_of}",
                variables,
            )
            plain_parts = [
                f"{process_label}工程で在庫停滞が検出されました。",
                f"基準日: {variables['as_of']}",
                f"閾値(>): {variables['min_quantity']}",
                f"連続暦日: {variables['stable_calendar_days']} 日",
                f"検出件数: {variables['item_count']} 件",
                f"送信者: {variables['sent_by']}",
                f"送信日時: {variables['sent_at']}",
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
                    sent_by_user_id=sent_by_user_id,
                )
                db.add(log)
                if result.success:
                    line_sent_count += 1
                    group_sent = True
                else:
                    line_failed.append(
                        {"line_user_id": recipient.line_user_id, "error": result.error or "送信失敗"}
                    )

        if group_sent:
            groups_sent.append(col)

    await db.commit()

    total_sent = email_sent_count + line_sent_count
    if total_sent == 0:
        err_parts = []
        if email_failed:
            err_parts.append(f"メール失敗 {len(email_failed)} 件")
        if line_failed:
            err_parts.append(f"LINE失敗 {len(line_failed)} 件")
        if is_auto:
            return {
                "success": True,
                "status": "no_sendable",
                "as_of": meta["as_of"],
                "total_sent": 0,
                "groups_skipped": groups_skipped,
                "email_failed": email_failed,
                "line_failed": line_failed,
                "message": "送信可能な工程なし",
            }
        if groups_skipped and not err_parts:
            raise HTTPException(
                status_code=400,
                detail="送信可能な工程がありません（受信者未設定・送信済み・チャネル未構成を確認してください）",
            )
        detail_parts: list[str] = []
        if email_failed:
            detail_parts.append(_friendly_delivery_error(email_failed, channel="メール"))
        if line_failed:
            detail_parts.append(_friendly_delivery_error(line_failed, channel="LINE"))
        raise HTTPException(
            status_code=400,
            detail="通知送信に失敗しました: " + (" / ".join(detail_parts) or "不明"),
        )

    has_failures = bool(email_failed or line_failed)
    return {
        "success": True,
        "status": "partial" if has_failures else "sent",
        "trigger": trigger,
        "as_of": meta["as_of"],
        "email_sent_count": email_sent_count,
        "line_sent_count": line_sent_count,
        "total_sent": total_sent,
        "groups_sent": groups_sent,
        "groups_skipped": groups_skipped,
        "email_failed": email_failed,
        "line_failed": line_failed,
        "message": _build_send_result_message(
            email_sent_count=email_sent_count,
            line_sent_count=line_sent_count,
            email_failed=email_failed,
            line_failed=line_failed,
        ),
    }
