-- 切断工程実績レポート：メール本文をプレビュー同型の summary_html に統一
UPDATE email_templates
SET body = '{summary_html}<p style="margin:12px 0 0;font-size:11px;color:#94a3b8;">※ 本メールは Smart-EMAP システムより自動送信されています。</p><p style="margin:4px 0 0;font-size:11px;color:#94a3b8;">送信者: {sent_by}　送信日時: {sent_at}</p>'
WHERE code = 'REPORT_CUTTING_DAILY_ACTUAL';
