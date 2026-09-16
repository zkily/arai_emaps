"""レポート定義の既定値（DB 未更新時の補正含む）"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.modules.reports.models import ReportDefinition

CUTTING_REPORT_CODE = "CUTTING_DAILY_ACTUAL"
CUTTING_DEFAULT_FORMAT = "pdf"
CUTTING_DEFAULT_DATE_RANGE = "this_month"

CUTTING_PARAMETER_SCHEMA: dict[str, Any] = {
    "fields": [
        {
            "key": "date_range",
            "label": "対象期間",
            "type": "date_range",
            "default": CUTTING_DEFAULT_DATE_RANGE,
            "presets": [
                "yesterday",
                "today",
                "last_week",
                "this_week",
                "last_month",
                "this_month",
                "custom",
            ],
        }
    ]
}


def cutting_report_needs_default_sync(definition: ReportDefinition) -> bool:
    if definition.report_code != CUTTING_REPORT_CODE:
        return False
    if definition.default_format != CUTTING_DEFAULT_FORMAT:
        return True
    schema = definition.parameter_schema or {}
    fields = schema.get("fields") or []
    if not fields:
        return True
    return fields[0].get("default") != CUTTING_DEFAULT_DATE_RANGE


def apply_cutting_report_defaults(definition: ReportDefinition) -> None:
    if definition.report_code != CUTTING_REPORT_CODE:
        return
    definition.default_format = CUTTING_DEFAULT_FORMAT
    definition.parameter_schema = deepcopy(CUTTING_PARAMETER_SCHEMA)


CUTTING_EMAIL_TEMPLATE_BODY = (
    '{summary_html}'
    '<p style="margin:12px 0 0;font-size:11px;color:#94a3b8;">'
    "※ 本メールは Smart-EMAP システムより自動送信されています。"
    "</p>"
    '<p style="margin:4px 0 0;font-size:11px;color:#94a3b8;">'
    "送信者: {sent_by}　送信日時: {sent_at}</p>"
)

PLAN_BASELINE_REPORT_CODE = "PLAN_BASELINE_WEEKLY"
PLAN_BASELINE_EVENT_CODE = "REPORT_PLAN_BASELINE_WEEKLY"
PLAN_BASELINE_EMAIL_TEMPLATE_BODY = CUTTING_EMAIL_TEMPLATE_BODY


async def ensure_cutting_email_template(db) -> None:
    from sqlalchemy import select

    from app.modules.system.settings_models import EmailTemplate

    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.code == "REPORT_CUTTING_DAILY_ACTUAL")
    )
    template = result.scalar_one_or_none()
    if template and template.body != CUTTING_EMAIL_TEMPLATE_BODY:
        template.body = CUTTING_EMAIL_TEMPLATE_BODY
        await db.commit()


async def ensure_plan_baseline_email_template(db) -> None:
    """ベースライン週次レポートのメールテンプレートが無ければ作成する。"""
    from sqlalchemy import select

    from app.modules.system.settings_models import EmailTemplate

    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.code == PLAN_BASELINE_EVENT_CODE)
    )
    template = result.scalar_one_or_none()
    if template:
        return
    db.add(
        EmailTemplate(
            code=PLAN_BASELINE_EVENT_CODE,
            name="生産計画ベースラインレポート",
            subject="【Smart-EMAP】{report_name} {period_label}（{record_count}件）",
            body=PLAN_BASELINE_EMAIL_TEMPLATE_BODY,
            event_code=PLAN_BASELINE_EVENT_CODE,
            language="ja",
            variables=["report_name", "period_label", "record_count", "summary_html", "sent_by", "sent_at"],
            is_active=True,
        )
    )
    await db.commit()
