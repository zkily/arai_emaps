-- 切断試作完了通知（備考に「試作」を含み完了済みの切断指示）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO notification_settings (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled, is_active)
VALUES
('CUTTING_TRIAL_COMPLETED', '切断試作完了', '切断指示-今日で備考に試作を含み完了済みのデータ', 0, 1, 0, 1, 1)
ON DUPLICATE KEY UPDATE event_name = VALUES(event_name), description = VALUES(description);

INSERT INTO email_templates (code, name, subject, body, event_code, language, variables, is_active)
VALUES
(
  'CUTTING_TRIAL_COMPLETED',
  '切断試作完了',
  '【Smart-EMAP】切断試作完了通知 {production_day}（{item_count}件）',
  '<p>切断指示（試作）の完了分をお知らせします。</p><p>対象生産日: {production_day}<br>件数: {item_count} 件<br>生産数合計: {total_quantity} 本</p>{item_list}<p>Smart-EMAP 生産管理システム</p>',
  'CUTTING_TRIAL_COMPLETED',
  'ja',
  '["production_day","item_count","total_quantity","item_list","item_list_text"]',
  1
)
ON DUPLICATE KEY UPDATE name = VALUES(name), subject = VALUES(subject), body = VALUES(body), variables = VALUES(variables);

SET FOREIGN_KEY_CHECKS = 1;
