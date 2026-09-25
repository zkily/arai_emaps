"""Apply migration 132: plan baseline weekly report (idempotent)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mysql.connector

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(ROOT))

from scripts.bootstrap_full_database import load_db_settings  # noqa: E402

EVENT_CODE = "REPORT_PLAN_BASELINE_WEEKLY"
REPORT_CODE = "PLAN_BASELINE_WEEKLY"
EMAIL_BODY = (
    "{summary_html}"
    '<p style="margin:12px 0 0;font-size:11px;color:#94a3b8;">'
    "※ 本メールは Smart-EMAP システムより自動送信されています。"
    "</p>"
    '<p style="margin:4px 0 0;font-size:11px;color:#94a3b8;">'
    "送信者: {sent_by}　送信日時: {sent_at}</p>"
)
PARAM_SCHEMA = {
    "fields": [
        {"key": "month", "label": "基準月", "type": "month", "default": "this_month"}
    ]
}


def main() -> int:
    host, port, user, password, db_name = load_db_settings(None)
    conn = mysql.connector.connect(
        host=host, port=port, user=user, password=password, database=db_name
    )
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO notification_settings
              (event_code, event_name, description, in_app_enabled, email_enabled,
               slack_enabled, line_enabled, is_active)
            VALUES (%s, %s, %s, 0, 1, 0, 0, 1)
            ON DUPLICATE KEY UPDATE
              event_name = VALUES(event_name),
              description = VALUES(description),
              email_enabled = VALUES(email_enabled),
              is_active = VALUES(is_active)
            """,
            (
                EVENT_CODE,
                "生産計画ベースラインレポート",
                "基準計画と実績の比較PDFを週次添付配信（金曜19:00）",
            ),
        )
        cur.execute(
            """
            INSERT INTO report_definitions
              (report_code, report_name, category, default_format, parameter_schema,
               event_code, description, is_active)
            VALUES (%s, %s, 'APS', 'pdf', %s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE
              report_name = VALUES(report_name),
              category = VALUES(category),
              default_format = VALUES(default_format),
              parameter_schema = VALUES(parameter_schema),
              event_code = VALUES(event_code),
              description = VALUES(description),
              is_active = VALUES(is_active)
            """,
            (
                REPORT_CODE,
                "生産計画ベースラインレポート",
                json.dumps(PARAM_SCHEMA, ensure_ascii=False),
                EVENT_CODE,
                "基準計画と実績の工程別比較をPDF添付で週次配信",
            ),
        )
        cur.execute(
            """
            INSERT INTO email_templates
              (code, name, subject, body, event_code, language, variables, is_active)
            VALUES (%s, %s, %s, %s, %s, 'ja', %s, 1)
            ON DUPLICATE KEY UPDATE
              name = VALUES(name),
              subject = VALUES(subject),
              body = VALUES(body),
              event_code = VALUES(event_code),
              variables = VALUES(variables),
              is_active = VALUES(is_active)
            """,
            (
                EVENT_CODE,
                "生産計画ベースラインレポート",
                "【Smart-EMAP】{report_name} {period_label}（{record_count}件）",
                EMAIL_BODY,
                EVENT_CODE,
                json.dumps(
                    ["report_name", "period_label", "record_count", "summary_html", "sent_by", "sent_at"],
                    ensure_ascii=False,
                ),
            ),
        )
        cur.execute(
            "SELECT id FROM report_schedules WHERE report_code=%s AND schedule_type='weekly' "
            "AND schedule_time='19:00:00' LIMIT 1",
            (REPORT_CODE,),
        )
        if cur.fetchone() is None:
            cur.execute(
                """
                INSERT INTO report_schedules
                  (report_code, schedule_type, schedule_time, schedule_config, parameters,
                   format, is_active, next_run_at)
                VALUES (%s, 'weekly', '19:00:00', %s, %s, 'pdf', 1, NULL)
                """,
                (
                    REPORT_CODE,
                    json.dumps({"weekday": 4}, ensure_ascii=False),
                    json.dumps({"month": "this_month"}, ensure_ascii=False),
                ),
            )
        conn.commit()
        cur.execute(
            "SELECT report_code, schedule_type, schedule_time, "
            "CAST(schedule_config AS CHAR), is_active FROM report_schedules "
            "WHERE report_code=%s",
            (REPORT_CODE,),
        )
        print("schedules:", cur.fetchall())
        cur.execute(
            "SELECT report_code, report_name FROM report_definitions WHERE report_code=%s",
            (REPORT_CODE,),
        )
        print("definitions:", cur.fetchall())
        print("OK")
        return 0
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
