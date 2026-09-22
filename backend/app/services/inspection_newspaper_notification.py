"""検査新聞紙通知（切断実績確定後、対象製品があれば検査工程へ自動メール）

品質管理ページで登録した対象製品が当日の切断実績に含まれる場合、
管理コード前13桁で同一バッチとみなし、cutting_management.planned_quantity（計画数）をメールする。
同一日・同一製品・同一バッチは、各受信者へ初めて届いたときだけ送信する。
一部の宛先が失敗しても、成功した宛先には再送しない。
"""
from __future__ import annotations

import html
from datetime import date, datetime

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import now_jst
from app.modules.system.settings_models import EmailSendLog, NotificationSetting
from app.services.email_service import (
    load_email_template,
    load_smtp_config,
    render_template,
    send_html_email,
)
from app.services.notification_recipient_service import (
    ResolvedRecipient,
    resolve_notification_recipients,
)

INSPECTION_NEWSPAPER_EVENT = "INSPECTION_NEWSPAPER_ALERT"
_REFERENCE_PREFIX = "inspection-newspaper"
BATCH_KEY_LEN = 13


def batch_key_from_management_code(management_code: str | None) -> str:
    return (management_code or "").strip()[:BATCH_KEY_LEN]


def build_reference_key(prod_day: date, product_cd: str, batch_key: str) -> str:
    return f"{_REFERENCE_PREFIX}:{prod_day.isoformat()}:{product_cd}:{batch_key}"


def parse_production_day(production_day: str) -> date:
    parts = production_day.strip().split("-")
    if len(parts) != 3:
        raise ValueError("production_day は YYYY-MM-DD で指定してください")
    return date(int(parts[0]), int(parts[1]), int(parts[2]))


async def _get_setting(db: AsyncSession) -> NotificationSetting | None:
    result = await db.execute(
        select(NotificationSetting).where(
            NotificationSetting.event_code == INSPECTION_NEWSPAPER_EVENT
        )
    )
    return result.scalar_one_or_none()


async def _fetch_matched_batches(db: AsyncSession, prod_day: date) -> list[dict]:
    """当日確定分 × 対象製品を、管理コード前13桁のバッチ単位で集計する。

    数量は実績の合計ではなく、当該管理コードが持つ計画数（planned_quantity）。
    同一前13桁の行は同じ計画数を持つため MAX を採用する。
    """
    sql = text(
        """
        SELECT
            cm.product_cd,
            MAX(COALESCE(NULLIF(t.product_name, ''), cm.product_cd)) AS product_name,
            LEFT(TRIM(cm.management_code), :batch_len) AS batch_key,
            GROUP_CONCAT(
                DISTINCT NULLIF(TRIM(cm.cutting_machine), '')
                ORDER BY cm.cutting_machine
                SEPARATOR '、'
            ) AS cutting_machine,
            MAX(COALESCE(cm.planned_quantity, 0)) AS quantity
        FROM cutting_management cm
        INNER JOIN quality_inspection_newspaper_products t
            ON t.product_cd = cm.product_cd
        WHERE cm.production_day = :production_day
          AND cm.production_completed_check = 1
          AND TRIM(IFNULL(cm.management_code, '')) <> ''
        GROUP BY cm.product_cd, LEFT(TRIM(cm.management_code), :batch_len)
        ORDER BY cm.product_cd, batch_key
        """
    )
    res = await db.execute(sql, {"production_day": prod_day, "batch_len": BATCH_KEY_LEN})
    rows = []
    for r in res.mappings().fetchall():
        item = dict(r)
        item["batch_key"] = batch_key_from_management_code(item.get("batch_key"))
        item["quantity"] = int(item.get("quantity") or 0)
        if item["batch_key"]:
            rows.append(item)
    return rows


def _html_cell(value: object) -> str:
    text = str(value or "").strip()
    return html.escape(text or "—")


def _build_product_table_html(rows: list[dict]) -> str:
    body_rows = "".join(
        "<tr>"
        f"<td>{_html_cell(r.get('product_cd'))}</td>"
        f"<td>{_html_cell(r.get('product_name'))}</td>"
        f"<td align='right'>{int(r.get('quantity') or 0):,} 本</td>"
        "</tr>"
        for r in rows
    )
    return (
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<tr><th>製品CD</th><th>製品名</th><th>計画数</th></tr>"
        f"{body_rows}</table>"
    )


async def _successful_recipient_emails(db: AsyncSession, keys: list[str]) -> dict[str, set[str]]:
    """reference_key ごとに、送信成功済みのメールアドレス（小文字）を返す。"""
    if not keys:
        return {}
    res = await db.execute(
        select(EmailSendLog.reference_key, EmailSendLog.recipient_email).where(
            EmailSendLog.event_code == INSPECTION_NEWSPAPER_EVENT,
            EmailSendLog.reference_key.in_(keys),
            EmailSendLog.status == "success",
        )
    )
    sent: dict[str, set[str]] = {}
    for key, email in res.all():
        if not key or not email:
            continue
        sent.setdefault(key, set()).add(str(email).strip().lower())
    return sent


def _recipient_email_set(recipients: list) -> set[str]:
    return {(r.email or "").strip().lower() for r in recipients if (r.email or "").strip()}


def _annotate_send_status(
    rows: list[dict],
    prod_day: date,
    success_by_key: dict[str, set[str]],
    recipient_emails: set[str],
) -> list[dict]:
    annotated = []
    for row in rows:
        key = build_reference_key(prod_day, str(row.get("product_cd") or ""), str(row.get("batch_key") or ""))
        delivered = success_by_key.get(key, set())
        item = dict(row)
        item["already_sent"] = bool(recipient_emails) and recipient_emails <= delivered
        item["delivered_count"] = len(recipient_emails & delivered)
        item["reference_key"] = key
        annotated.append(item)
    return annotated


async def get_inspection_newspaper_preview(db: AsyncSession, *, production_day: str) -> dict:
    """指定生産日でいま送信するとどうなるかのプレビュー（バッチ単位）。"""
    prod_day = parse_production_day(production_day)

    setting = await _get_setting(db)
    enabled = bool(setting and setting.is_active and setting.email_enabled)

    rows = await _fetch_matched_batches(db, prod_day)
    keys = [
        build_reference_key(prod_day, str(r.get("product_cd") or ""), str(r.get("batch_key") or ""))
        for r in rows
    ]
    recipients = await resolve_notification_recipients(db, INSPECTION_NEWSPAPER_EVENT)
    success_by_key = await _successful_recipient_emails(db, keys)
    rows = _annotate_send_status(rows, prod_day, success_by_key, _recipient_email_set(recipients))

    template = await load_email_template(db, INSPECTION_NEWSPAPER_EVENT)
    smtp = await load_smtp_config(db)

    pending_rows = [r for r in rows if not r["already_sent"]]
    product_count = len({r["product_cd"] for r in rows})
    total_quantity = sum(int(r.get("quantity") or 0) for r in rows)
    already_sent = bool(rows) and not pending_rows

    return {
        "success": True,
        "production_day": prod_day.isoformat(),
        "enabled": enabled,
        "smtp_configured": smtp is not None,
        "template_subject": template.subject if template else None,
        "matched_rows": rows,
        "matched_count": len(rows),
        "pending_count": len(pending_rows),
        "product_count": product_count,
        "total_quantity": total_quantity,
        "recipients": [
            {"email": r.email, "name": r.name, "source": r.source} for r in recipients
        ],
        "recipient_count": len(recipients),
        "already_sent": already_sent,
        "can_send": (
            enabled
            and smtp is not None
            and template is not None
            and bool(pending_rows)
            and bool(recipients)
        ),
    }


def _pending_rows_for_recipient(
    rows: list[dict],
    email: str,
    success_by_key: dict[str, set[str]],
    *,
    force: bool,
) -> list[dict]:
    if force:
        return list(rows)
    normalized = email.strip().lower()
    return [
        row
        for row in rows
        if normalized not in success_by_key.get(str(row.get("reference_key") or ""), set())
    ]


async def _send_inspection_newspaper_notification_unlocked(
    db: AsyncSession,
    *,
    prod_day: date,
    confirmed_by: str = "",
    sent_by_user_id: int | None = None,
    force: bool = False,
) -> dict:
    setting = await _get_setting(db)
    if not setting or not setting.is_active or not setting.email_enabled:
        return {"success": True, "skipped": True, "reason": "通知が無効です", "sent_count": 0}

    rows = await _fetch_matched_batches(db, prod_day)
    if not rows:
        return {"success": True, "skipped": True, "reason": "対象製品がありません", "sent_count": 0}

    keys = [
        build_reference_key(prod_day, str(r.get("product_cd") or ""), str(r.get("batch_key") or ""))
        for r in rows
    ]
    recipients = await resolve_notification_recipients(db, INSPECTION_NEWSPAPER_EVENT)
    if not recipients:
        return {"success": False, "skipped": True, "reason": "受信者が登録されていません", "sent_count": 0}

    success_by_key = await _successful_recipient_emails(db, keys)
    rows = _annotate_send_status(rows, prod_day, success_by_key, _recipient_email_set(recipients))
    deliveries: list[tuple[ResolvedRecipient, list[dict]]] = []
    for recipient in recipients:
        pending = _pending_rows_for_recipient(
            rows,
            recipient.email,
            success_by_key,
            force=force,
        )
        if pending:
            deliveries.append((recipient, pending))
    if not deliveries:
        return {
            "success": True,
            "skipped": True,
            "reason": "本日このバッチは送信済みです",
            "sent_count": 0,
        }

    smtp = await load_smtp_config(db)
    if smtp is None:
        return {"success": False, "skipped": True, "reason": "SMTP が未設定です", "sent_count": 0}

    template = await load_email_template(db, INSPECTION_NEWSPAPER_EVENT)
    if template is None:
        return {"success": False, "skipped": True, "reason": "メールテンプレートがありません", "sent_count": 0}

    confirmed_at = now_jst()
    confirmed_at_str = (
        confirmed_at.strftime("%Y-%m-%d %H:%M")
        if isinstance(confirmed_at, datetime)
        else str(confirmed_at)
    )
    sent_count = 0
    failed: list[dict[str, str]] = []
    sent_batch_keys: set[str] = set()
    for recipient, target_rows in deliveries:
        product_count = len({r["product_cd"] for r in target_rows})
        total_quantity = sum(int(r.get("quantity") or 0) for r in target_rows)
        variables = {
            "production_day": prod_day.isoformat(),
            "product_table": _build_product_table_html(target_rows),
            "product_count": product_count,
            "total_quantity": f"{total_quantity:,}",
            "confirmed_by": confirmed_by,
            "confirmed_at": confirmed_at_str,
        }
        subject = render_template(template.subject, variables)
        body = render_template(template.body, variables)
        result = await send_html_email(smtp, recipient.email, subject, body)
        for row in target_rows:
            sent_batch_keys.add(str(row.get("reference_key") or ""))
            db.add(
                EmailSendLog(
                    event_code=INSPECTION_NEWSPAPER_EVENT,
                    reference_key=row["reference_key"],
                    recipient_email=recipient.email,
                    subject=subject,
                    status="success" if result.success else "failed",
                    error_message=result.error,
                    sent_by_user_id=sent_by_user_id,
                )
            )
        if result.success:
            sent_count += 1
        else:
            failed.append({"email": recipient.email, "error": result.error or "送信失敗"})
    await db.commit()

    included_rows = [r for r in rows if str(r.get("reference_key") or "") in sent_batch_keys]
    product_count = len({r["product_cd"] for r in included_rows})
    total_quantity = sum(int(r.get("quantity") or 0) for r in included_rows)
    message = f"メール {sent_count} 件を送信しました（{len(included_rows)} バッチ）"
    if failed:
        message += f"（失敗 {len(failed)} 件）"
    return {
        "success": sent_count > 0,
        "skipped": False,
        "sent_count": sent_count,
        "failed": failed,
        "message": message,
        "product_count": product_count,
        "total_quantity": total_quantity,
        "batch_count": len(included_rows),
    }


async def send_inspection_newspaper_notification(
    db: AsyncSession,
    *,
    production_day: str,
    confirmed_by: str = "",
    sent_by_user_id: int | None = None,
    force: bool = False,
    lock_wait_sec: int = 10,
) -> dict:
    """検査新聞紙通知メールを送信する。

    自動トリガーは、当日・製品・管理コード前13桁について未着の受信者だけ送る。
    force=True の手動再送信は当日バッチを全受信者へ再送する。
    """
    from app.core.database import engine

    prod_day = parse_production_day(production_day)
    lock_name = f"insp-np:{prod_day.isoformat()}"
    async with engine.connect() as lock_conn:
        got = (
            await lock_conn.execute(
                text("SELECT GET_LOCK(:name, :wait)"),
                {"name": lock_name, "wait": int(lock_wait_sec)},
            )
        ).scalar()
        if int(got or 0) != 1:
            return {
                "success": False,
                "skipped": True,
                "reason": "別の送信処理が実行中です。しばらくしてから再度お試しください。",
                "sent_count": 0,
            }
        try:
            return await _send_inspection_newspaper_notification_unlocked(
                db,
                prod_day=prod_day,
                confirmed_by=confirmed_by,
                sent_by_user_id=sent_by_user_id,
                force=force,
            )
        finally:
            await lock_conn.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": lock_name})


async def run_inspection_newspaper_auto_notify(production_day: str, confirmed_by: str = "") -> None:
    """切断実績確定後のバックグラウンド自動送信（独立セッション・例外握りつぶし）。"""
    from app.core.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            result = await send_inspection_newspaper_notification(
                db,
                production_day=production_day,
                confirmed_by=confirmed_by,
                lock_wait_sec=180,
            )
            if result.get("skipped"):
                logger.info(
                    "検査新聞紙通知 skip production_day={} reason={}",
                    production_day,
                    result.get("reason"),
                )
            else:
                logger.info(
                    "検査新聞紙通知 sent production_day={} sent={} batches={} failed={}",
                    production_day,
                    result.get("sent_count"),
                    result.get("batch_count"),
                    len(result.get("failed") or []),
                )
    except Exception:
        logger.exception("検査新聞紙通知の自動送信に失敗 production_day={}", production_day)
