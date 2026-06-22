-- ユーザー個人 TODO（ヘッダー）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `user_todos` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'ユーザーID',
  `content` varchar(500) NOT NULL COMMENT 'TODO内容',
  `is_done` tinyint NOT NULL DEFAULT 0 COMMENT '完了フラグ 0=未完了 1=完了',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `completed_at` datetime DEFAULT NULL COMMENT '完了日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_user_done_created` (`user_id`, `is_done`, `created_at`),
  CONSTRAINT `fk_user_todos_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザー個人TODO';

SET FOREIGN_KEY_CHECKS = 1;
