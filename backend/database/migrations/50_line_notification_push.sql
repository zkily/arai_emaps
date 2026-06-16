-- LINE プッシュ通知：受信者 line_user_id・送信ログ・実績確定イベント LINE 有効化
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `notification_recipients`
  ADD COLUMN `line_user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'LINE User ID（recipient_type=line）' AFTER `email`;

CREATE TABLE IF NOT EXISTS `line_send_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `event_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'イベントコード',
  `reference_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '参照キー',
  `line_user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'LINE User ID',
  `message_preview` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'メッセージ先頭（ログ用）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'success|failed',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'エラー内容',
  `sent_by_user_id` int NULL DEFAULT NULL COMMENT '送信者 users.id',
  `sent_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '送信日時',
  PRIMARY KEY (`id`),
  INDEX `idx_line_send_logs_event_ref` (`event_code`, `reference_key`),
  INDEX `idx_line_send_logs_sent_at` (`sent_at`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'LINE送信ログ' ROW_FORMAT = Dynamic;

UPDATE notification_settings
SET line_enabled = 1
WHERE event_code IN ('CUTTING_ACTUAL_CONFIRMED', 'CHAMFERING_ACTUAL_CONFIRMED');

SET FOREIGN_KEY_CHECKS = 1;
