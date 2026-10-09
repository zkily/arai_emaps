-- TABLE: fin_year_end_adjustment
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_year_end_adjustment` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `employee_id` int DEFAULT NULL COMMENT '社員ID',
  `target_year` int NOT NULL COMMENT '対象年',
  `total_income` decimal(18,2) DEFAULT '0.00' COMMENT '給与収入',
  `deduction_total` decimal(18,2) DEFAULT '0.00' COMMENT '所得控除合計',
  `tax_settled` decimal(18,2) DEFAULT '0.00' COMMENT '年調後税額',
  `refund_amount` decimal(18,2) DEFAULT '0.00' COMMENT '値（還付/追徴）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'draft' COMMENT '状態（下書き/確定）',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_year_end_adjustment_employee_id` (`employee_id`),
  KEY `idx_fin_year_end_adjustment_target_year` (`target_year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='年末調整';

SET FOREIGN_KEY_CHECKS = 1;
