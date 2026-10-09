-- TABLE: user_page_visits
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `user_page_visits` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'ユーザーID',
  `path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ルートパス',
  `visit_count` int NOT NULL DEFAULT '1' COMMENT '訪問回数',
  `last_visited_at` datetime NOT NULL COMMENT '最終訪問日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_path` (`user_id`,`path`),
  KEY `idx_user_freq` (`user_id`,`visit_count`,`last_visited_at`),
  CONSTRAINT `fk_visit_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザー別ページ訪問統計';

SET FOREIGN_KEY_CHECKS = 1;
