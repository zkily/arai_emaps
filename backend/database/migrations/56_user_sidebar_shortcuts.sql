-- サイドバー常用ページ：ユーザー別ピン留め・訪問統計
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `user_pinned_pages` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'ユーザーID',
  `path` varchar(255) NOT NULL COMMENT 'ルートパス',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '表示順',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_path` (`user_id`, `path`),
  KEY `idx_user_sort` (`user_id`, `sort_order`),
  CONSTRAINT `fk_pinned_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザー別サイドバー固定ページ';

CREATE TABLE IF NOT EXISTS `user_page_visits` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'ユーザーID',
  `path` varchar(255) NOT NULL COMMENT 'ルートパス',
  `visit_count` int NOT NULL DEFAULT 1 COMMENT '訪問回数',
  `last_visited_at` datetime NOT NULL COMMENT '最終訪問日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_path` (`user_id`, `path`),
  KEY `idx_user_freq` (`user_id`, `visit_count`, `last_visited_at`),
  CONSTRAINT `fk_visit_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザー別ページ訪問統計';

SET FOREIGN_KEY_CHECKS = 1;
