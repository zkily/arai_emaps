-- TABLE: email_send_logs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `email_send_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `event_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'イベントコード',
  `reference_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '参照キー（例 cutting:2026-06-16）',
  `recipient_email` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '送信先メール',
  `subject` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '件名',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'success|failed',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'エラー内容',
  `sent_by_user_id` int DEFAULT NULL COMMENT '送信者 users.id',
  `sent_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '送信日時',
  PRIMARY KEY (`id`),
  KEY `idx_email_send_logs_event_ref` (`event_code`,`reference_key`),
  KEY `idx_email_send_logs_sent_at` (`sent_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='メール送信ログ';

SET FOREIGN_KEY_CHECKS = 1;
