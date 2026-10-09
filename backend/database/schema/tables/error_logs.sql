-- TABLE: error_logs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `error_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
  `level` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'レベル（ERROR/WARN/INFO）',
  `source` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ソース（サービス名・ファイル名）',
  `message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'エラーメッセージ',
  `stack_trace` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'スタックトレース',
  `user_id` int DEFAULT NULL COMMENT 'ユーザーID',
  `request_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'リクエストID',
  `extra_data` json DEFAULT NULL COMMENT '追加データ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_error_logs_timestamp` (`timestamp`),
  KEY `idx_error_logs_level` (`level`),
  KEY `idx_error_logs_source` (`source`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='エラーログテーブル';

SET FOREIGN_KEY_CHECKS = 1;
