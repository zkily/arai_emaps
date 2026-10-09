-- TABLE: fin_payroll_run_line
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_payroll_run_line` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `run_id` bigint NOT NULL COMMENT '親レコードID',
  `employee_id` int DEFAULT NULL COMMENT '社員ID',
  `employee_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '社員名',
  `gross_amount` decimal(18,2) DEFAULT '0.00' COMMENT '総支給',
  `deduction_amount` decimal(18,2) DEFAULT '0.00' COMMENT '控除合計',
  `net_amount` decimal(18,2) DEFAULT '0.00' COMMENT '差引支給',
  `detail_json` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '項目別明細',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_payroll_run_line_run_id` (`run_id`),
  KEY `idx_fin_payroll_run_line_employee_id` (`employee_id`),
  CONSTRAINT `fk_fin_payroll_run_line_run_id` FOREIGN KEY (`run_id`) REFERENCES `fin_payroll_run` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='給与明細';

SET FOREIGN_KEY_CHECKS = 1;
