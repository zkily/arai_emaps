-- TABLE: integration_configs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `integration_configs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `service_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'サービスタイプ（slack/line/teams等）',
  `config` json NOT NULL COMMENT '設定情報（webhook_url, token等）',
  `is_enabled` tinyint(1) DEFAULT '0' COMMENT '有効フラグ',
  `last_test_at` datetime DEFAULT NULL COMMENT '最終テスト日時',
  `last_test_result` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '最終テスト結果',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `service_type` (`service_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外部連携設定テーブル';

SET FOREIGN_KEY_CHECKS = 1;
