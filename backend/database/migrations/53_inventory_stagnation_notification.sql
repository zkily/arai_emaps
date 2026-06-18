-- 在庫停滞アラート通知（工程別メール・LINE 扇出）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `notification_recipients`
  ADD COLUMN `inventory_column` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL
    COMMENT '在庫列スコープ（INVENTORY_STAGNATION 用。空=全工程）'
    AFTER `machine_cd`;

INSERT INTO notification_settings (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled, is_active)
VALUES
('INVENTORY_STAGNATION', '在庫停滞アラート', '在庫停滞監視で検出した工程別停滞在庫の通知', 0, 1, 0, 1, 1)
ON DUPLICATE KEY UPDATE event_name = VALUES(event_name), description = VALUES(description);

INSERT INTO email_templates (code, name, subject, body, event_code, language, variables, is_active)
VALUES
(
  'INVENTORY_STAGNATION',
  '在庫停滞アラート',
  '【Smart-EMAP】{process_label} 在庫停滞アラート {as_of}（{item_count}件）',
  '<p>{process_label}工程で在庫停滞が検出されました。</p><p>基準日: {as_of}<br>閾値(&gt;): {min_quantity}<br>連続暦日: {stable_calendar_days} 日<br>検出件数: {item_count} 件<br>送信者: {sent_by}<br>送信日時: {sent_at}</p>{item_table}<p>Smart-EMAP 生産管理システム</p>',
  'INVENTORY_STAGNATION',
  'ja',
  '["process_label","as_of","min_quantity","stable_calendar_days","item_count","item_table","item_list_text","sent_by","sent_at"]',
  1
)
ON DUPLICATE KEY UPDATE name = VALUES(name), subject = VALUES(subject), body = VALUES(body), variables = VALUES(variables);

SET FOREIGN_KEY_CHECKS = 1;
