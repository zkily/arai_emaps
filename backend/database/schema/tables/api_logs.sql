-- TABLE: api_logs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `api_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
  `method` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'HTTPメソッド（GET/POST/PUT/DELETE）',
  `endpoint` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'エンドポイント',
  `status_code` int NOT NULL COMMENT 'HTTPステータスコード',
  `duration` int DEFAULT NULL COMMENT '応答時間（ミリ秒）',
  `client` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'クライアント（Web Frontend/Mobile App等）',
  `user_id` int DEFAULT NULL COMMENT 'ユーザーID',
  `ip_address` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IPアドレス',
  `request_body` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'リクエストボディ',
  `response_body` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'レスポンスボディ（エラー時のみ）',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'エラーメッセージ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_api_logs_timestamp` (`timestamp`),
  KEY `idx_api_logs_endpoint` (`endpoint`(200)),
  KEY `idx_api_logs_status` (`status_code`),
  KEY `idx_api_logs_method` (`method`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API連携ログテーブル';

SET FOREIGN_KEY_CHECKS = 1;
