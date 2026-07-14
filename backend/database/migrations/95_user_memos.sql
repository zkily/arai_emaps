-- ユーザー個人メモ（カレンダー・リマインダー）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `user_memos` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'ユーザーID',
  `title` varchar(200) NOT NULL COMMENT 'タイトル',
  `content` varchar(2000) DEFAULT NULL COMMENT '本文',
  `memo_date` date NOT NULL COMMENT 'カレンダー日付',
  `memo_time` time DEFAULT NULL COMMENT '時刻（NULL=終日）',
  `remind_at` datetime DEFAULT NULL COMMENT 'リマインド発火時刻（JST）',
  `remind_offset_minutes` int DEFAULT NULL COMMENT '事前リマインド分数',
  `color` varchar(20) DEFAULT NULL COMMENT '色ラベル',
  `status` tinyint NOT NULL DEFAULT 0 COMMENT '0=通常 1=完了',
  `reminded_at` datetime DEFAULT NULL COMMENT 'リマインド済み時刻',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_user_memo_date` (`user_id`, `memo_date`),
  KEY `idx_user_remind` (`user_id`, `status`, `remind_at`, `reminded_at`),
  CONSTRAINT `fk_user_memos_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザー個人メモ';

SET FOREIGN_KEY_CHECKS = 1;
