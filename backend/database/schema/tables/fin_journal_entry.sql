-- TABLE: fin_journal_entry
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_journal_entry` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `journal_no` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '仕訳番号',
  `entry_date` date NOT NULL COMMENT '仕訳日',
  `period_ym` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '計上年月',
  `entry_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'manual' COMMENT '種別（手動/売上/仕入/移動/製造/減価償却/給与）',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '摘要',
  `total_debit` decimal(18,2) DEFAULT '0.00' COMMENT '借方合計',
  `total_credit` decimal(18,2) DEFAULT '0.00' COMMENT '貸方合計',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'draft' COMMENT '状態（下書き/転記済/取消）',
  `source_id` bigint DEFAULT NULL COMMENT '仕訳ソースID',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_journal_entry_journal_no` (`journal_no`),
  KEY `idx_fin_journal_entry_entry_date` (`entry_date`),
  KEY `idx_fin_journal_entry_period_ym` (`period_ym`),
  KEY `idx_fin_journal_entry_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='仕訳ヘッダ';

SET FOREIGN_KEY_CHECKS = 1;
