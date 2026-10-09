-- TABLE: fin_payroll_run
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_payroll_run` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `run_no` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '給与計算番号',
  `target_month` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '対象年月',
  `pay_date` date DEFAULT NULL COMMENT '支給日',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'draft' COMMENT '状態（下書き/計算済/確定/支払済）',
  `total_gross` decimal(18,2) DEFAULT '0.00' COMMENT '総支給',
  `total_deduction` decimal(18,2) DEFAULT '0.00' COMMENT '総控除',
  `total_net` decimal(18,2) DEFAULT '0.00' COMMENT '差引支給',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_payroll_run_run_no` (`run_no`),
  KEY `idx_fin_payroll_run_target_month` (`target_month`),
  KEY `idx_fin_payroll_run_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='給与計算';

SET FOREIGN_KEY_CHECKS = 1;
