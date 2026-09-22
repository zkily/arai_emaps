-- ユーザー個人イベント（カレンダー）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `user_events` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'ユーザーID',
  `title` varchar(200) NOT NULL COMMENT 'タイトル',
  `description` varchar(2000) DEFAULT NULL COMMENT '詳細',
  `location` varchar(255) DEFAULT NULL COMMENT '場所',
  `start_at` datetime NOT NULL COMMENT '開始日時',
  `end_at` datetime NOT NULL COMMENT '終了日時',
  `all_day` tinyint NOT NULL DEFAULT 0 COMMENT '1=終日',
  `color` varchar(20) DEFAULT NULL COMMENT '色ラベル',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_user_event_range` (`user_id`, `start_at`, `end_at`),
  CONSTRAINT `fk_user_events_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザー個人イベント';

SET FOREIGN_KEY_CHECKS = 1;
