-- TABLE: operation_logs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `operation_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
  `user_id` int DEFAULT NULL COMMENT 'ユーザーID',
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ユーザー名',
  `action` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作（login/logout/create/update/delete）',
  `module` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'モジュール名',
  `target` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '対象（例: 受注番号: SO-202602-0156）',
  `target_id` int DEFAULT NULL COMMENT '対象レコードID',
  `ip_address` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IPアドレス',
  `user_agent` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'ユーザーエージェント',
  `details` json DEFAULT NULL COMMENT '詳細情報（変更前後の値など）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_operation_logs_timestamp` (`timestamp`),
  KEY `idx_operation_logs_user` (`user_id`),
  KEY `idx_operation_logs_action` (`action`),
  KEY `idx_operation_logs_module` (`module`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作ログテーブル';

SET FOREIGN_KEY_CHECKS = 1;
