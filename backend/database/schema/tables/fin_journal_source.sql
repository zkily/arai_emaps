-- TABLE: fin_journal_source
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_journal_source` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `source_type` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'イベント種別（売上計上等）',
  `source_module` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '連携元（ERP/経費/給与）',
  `source_ref` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '元伝票番号またはID',
  `event_date` date DEFAULT NULL COMMENT '事象日',
  `amount` decimal(18,2) DEFAULT '0.00' COMMENT '金額',
  `payload_json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '連携ペイロード',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'pending' COMMENT '状態（未生成/生成済/スキップ）',
  `journal_entry_id` bigint DEFAULT NULL COMMENT '生成先仕訳ID',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_journal_source_source_type` (`source_type`),
  KEY `idx_fin_journal_source_source_ref` (`source_ref`),
  KEY `idx_fin_journal_source_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='仕訳連携ソース';

SET FOREIGN_KEY_CHECKS = 1;
