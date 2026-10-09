-- TABLE: fin_accounting_period
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_accounting_period` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `fiscal_year_id` bigint DEFAULT NULL COMMENT '会計年度',
  `year_month` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '年月（YYYY-MM）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'open' COMMENT '状態（open/closing/closed）',
  `closed_at` datetime DEFAULT NULL COMMENT '締め日時',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_accounting_period_fiscal_year_id` (`fiscal_year_id`),
  KEY `idx_fin_accounting_period_year_month` (`year_month`),
  CONSTRAINT `fk_fin_accounting_period_fiscal_year_id` FOREIGN KEY (`fiscal_year_id`) REFERENCES `fin_fiscal_year` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会計期間（月次）';

SET FOREIGN_KEY_CHECKS = 1;
