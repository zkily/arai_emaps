-- TABLE: order_log
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `order_log` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `order_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '受注タイプ（monthly/daily）',
  `order_id` int NOT NULL COMMENT '受注ID',
  `action` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作（create/update/delete/sync）',
  `old_data` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '変更前データ（JSON）',
  `new_data` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '変更後データ（JSON）',
  `user_id` int DEFAULT NULL COMMENT 'ユーザーID',
  `user_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ユーザー名',
  `ip_address` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IPアドレス',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_order_type` (`order_type`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_action` (`action`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='受注ログ';

SET FOREIGN_KEY_CHECKS = 1;
