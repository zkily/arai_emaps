-- 生産計画ベースライン週次レポート（金曜19:00定時配信）
-- 適用: py backend/scripts/apply_plan_baseline_weekly_report_migration.py
-- （メール本文に ';' を含むため、本ファイルの単純セミコロン分割実行は非推奨）
SET NAMES utf8mb4;

INSERT INTO notification_settings
  (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled, is_active)
VALUES
  (
    'REPORT_PLAN_BASELINE_WEEKLY',
    '生産計画ベースラインレポート',
    '基準計画と実績の比較PDFを週次添付配信（金曜19:00）',
    0, 1, 0, 0, 1
  )
ON DUPLICATE KEY UPDATE
  event_name = VALUES(event_name),
  description = VALUES(description),
  email_enabled = VALUES(email_enabled),
  is_active = VALUES(is_active);

INSERT INTO report_definitions
  (report_code, report_name, category, default_format, parameter_schema, event_code, description, is_active)
VALUES
  (
    'PLAN_BASELINE_WEEKLY',
    '生産計画ベースラインレポート',
    'APS',
    'pdf',
    '{"fields":[{"key":"month","label":"基準月","type":"month","default":"this_month"}]}',
    'REPORT_PLAN_BASELINE_WEEKLY',
    '基準計画と実績の工程別比較をPDF添付で週次配信',
    1
  )
ON DUPLICATE KEY UPDATE
  report_name = VALUES(report_name),
  category = VALUES(category),
  default_format = VALUES(default_format),
  parameter_schema = VALUES(parameter_schema),
  event_code = VALUES(event_code),
  description = VALUES(description),
  is_active = VALUES(is_active);

-- email_templates / report_schedules は apply_plan_baseline_weekly_report_migration.py で投入推奨
