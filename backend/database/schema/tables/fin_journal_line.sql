-- TABLE: fin_journal_line
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_journal_line` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `entry_id` bigint NOT NULL COMMENT '親レコードID',
  `line_no` int DEFAULT '1' COMMENT '行番号',
  `account_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '勘定科目',
  `account_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '科目名',
  `debit` decimal(18,2) DEFAULT '0.00' COMMENT '借方',
  `credit` decimal(18,2) DEFAULT '0.00' COMMENT '貸方',
  `tax_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '税区分',
  `tax_amount` decimal(18,2) DEFAULT '0.00' COMMENT '消費税額',
  `department_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '部門',
  `partner_id` int DEFAULT NULL COMMENT '取引先',
  `remarks` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_journal_line_entry_id` (`entry_id`),
  KEY `idx_fin_journal_line_account_code` (`account_code`),
  CONSTRAINT `fk_fin_journal_line_entry_id` FOREIGN KEY (`entry_id`) REFERENCES `fin_journal_entry` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='仕訳明細';

SET FOREIGN_KEY_CHECKS = 1;
