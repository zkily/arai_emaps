-- TABLE: notification_settings
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `notification_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `event_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'イベントコード',
  `event_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'イベント名',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '説明',
  `in_app_enabled` tinyint(1) DEFAULT '1' COMMENT 'アプリ内通知有効',
  `email_enabled` tinyint(1) DEFAULT '0' COMMENT 'メール通知有効',
  `slack_enabled` tinyint(1) DEFAULT '0' COMMENT 'Slack通知有効',
  `line_enabled` tinyint(1) DEFAULT '0' COMMENT 'LINE通知有効',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '有効フラグ',
  `auto_schedule_enabled` tinyint(1) NOT NULL DEFAULT '0' COMMENT '自動スケジュール有効',
  `auto_schedule_time` time DEFAULT NULL COMMENT '自動実行時刻（JST）',
  `schedule_config` json DEFAULT NULL COMMENT '自動実行パラメータ JSON',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `event_code` (`event_code`),
  KEY `idx_notification_settings_event` (`event_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知設定テーブル';

SET FOREIGN_KEY_CHECKS = 1;
