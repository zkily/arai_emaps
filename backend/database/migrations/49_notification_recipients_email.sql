-- 通知受信者（方案 B：独立表）・メール送信ログ・実績確定通知イベント
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `notification_recipients` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `event_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'イベントコード',
  `recipient_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user' COMMENT 'user|email|role',
  `user_id` int NULL DEFAULT NULL COMMENT 'users.id（recipient_type=user）',
  `email` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '直接メール（recipient_type=email）',
  `role` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロール（recipient_type=role）',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備コード（任意・将来拡張）',
  `display_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '表示名（email 直接指定時）',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  INDEX `idx_notification_recipients_event` (`event_code`),
  INDEX `idx_notification_recipients_user` (`user_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '通知受信者' ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `email_send_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `event_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'イベントコード',
  `reference_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '参照キー（例 cutting:2026-06-16）',
  `recipient_email` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '送信先メール',
  `subject` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '件名',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'success|failed',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'エラー内容',
  `sent_by_user_id` int NULL DEFAULT NULL COMMENT '送信者 users.id',
  `sent_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '送信日時',
  PRIMARY KEY (`id`),
  INDEX `idx_email_send_logs_event_ref` (`event_code`, `reference_key`),
  INDEX `idx_email_send_logs_sent_at` (`sent_at`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'メール送信ログ' ROW_FORMAT = Dynamic;

INSERT INTO notification_settings (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled, is_active)
VALUES
('CUTTING_ACTUAL_CONFIRMED', '切断実績確定', '切断指示の実績確定完了時', 0, 1, 0, 0, 1),
('CHAMFERING_ACTUAL_CONFIRMED', '面取実績確定', '面取指示の実績確定完了時', 0, 1, 0, 0, 1)
ON DUPLICATE KEY UPDATE event_name = VALUES(event_name), description = VALUES(description);

INSERT INTO email_templates (code, name, subject, body, event_code, language, variables, is_active)
VALUES
(
  'CUTTING_ACTUAL_CONFIRMED',
  '切断実績確定',
  '【Smart-EMAP】切断実績確定 {production_day}（{total_quantity}本）',
  '<p>切断実績が確定されました。</p><p>生産日: {production_day}<br>登録件数: {inserted_count} 件<br>数量合計: {total_quantity} 本<br>確定者: {confirmed_by}<br>確定日時: {confirmed_at}</p>{machine_summary}<p>Smart-EMAP 生産管理システム</p>',
  'CUTTING_ACTUAL_CONFIRMED',
  'ja',
  '["production_day","inserted_count","total_quantity","confirmed_by","confirmed_at","machine_summary"]',
  1
),
(
  'CHAMFERING_ACTUAL_CONFIRMED',
  '面取実績確定',
  '【Smart-EMAP】面取実績確定 {production_day}（{total_quantity}本）',
  '<p>面取実績が確定されました。</p><p>生産日: {production_day}<br>登録件数: {inserted_count} 件<br>数量合計: {total_quantity} 本<br>確定者: {confirmed_by}<br>確定日時: {confirmed_at}</p>{machine_summary}<p>Smart-EMAP 生産管理システム</p>',
  'CHAMFERING_ACTUAL_CONFIRMED',
  'ja',
  '["production_day","inserted_count","total_quantity","confirmed_by","confirmed_at","machine_summary"]',
  1
)
ON DUPLICATE KEY UPDATE name = VALUES(name), subject = VALUES(subject), body = VALUES(body);

SET FOREIGN_KEY_CHECKS = 1;
