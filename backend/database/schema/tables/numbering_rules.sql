-- TABLE: numbering_rules
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `numbering_rules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ルールコード（例: SALES_ORDER）',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ルール名（例: 受注番号）',
  `prefix` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'プレフィックス（例: SO）',
  `format` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'フォーマット（例: {PREFIX}-{YYYY}{MM}-{SEQ:4}）',
  `start_number` int NOT NULL DEFAULT '1' COMMENT '連番開始値',
  `increment` int NOT NULL DEFAULT '1' COMMENT '連番増分',
  `current_number` int NOT NULL DEFAULT '0' COMMENT '現在の連番',
  `reset_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'monthly' COMMENT 'リセットタイミング（never/daily/monthly/yearly）',
  `last_reset_date` date DEFAULT NULL COMMENT '最終リセット日',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '有効フラグ',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '説明',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `idx_numbering_rules_code` (`code`),
  KEY `idx_numbering_rules_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='採番ルールテーブル';

SET FOREIGN_KEY_CHECKS = 1;
