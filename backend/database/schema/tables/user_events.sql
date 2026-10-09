-- TABLE: user_events
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `user_events` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'ユーザーID',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'タイトル',
  `description` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '詳細',
  `location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '場所',
  `start_at` datetime NOT NULL COMMENT '開始日時',
  `end_at` datetime NOT NULL COMMENT '終了日時',
  `all_day` tinyint NOT NULL DEFAULT '0' COMMENT '1=終日',
  `color` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '色ラベル',
  `visibility` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'department' COMMENT 'self=個人 department=部内 all=全社',
  `recurrence_rule` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'daily|weekly|monthly|yearly',
  `recurrence_until` date DEFAULT NULL COMMENT '繰り返し終了日',
  `recurrence_exdates` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '除外発生日 JSON ["YYYY-MM-DD",...]',
  `remind_offset_minutes` int DEFAULT NULL COMMENT '事前リマインド分数（NULL=無効）',
  `remind_at` datetime DEFAULT NULL COMMENT '次回リマインド発火時刻',
  `reminded_at` datetime DEFAULT NULL COMMENT 'リマインド済み時刻',
  `last_reminded_occurrence` date DEFAULT NULL COMMENT '繰り返し：最後に確認した発生日',
  `reminded_dates` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '確認済み発生日 JSON ["YYYY-MM-DD",...]',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_user_event_range` (`user_id`,`start_at`,`end_at`),
  CONSTRAINT `fk_user_events_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザー個人イベント';

SET FOREIGN_KEY_CHECKS = 1;
