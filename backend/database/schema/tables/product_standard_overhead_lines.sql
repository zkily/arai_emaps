-- TABLE: product_standard_overhead_lines
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_standard_overhead_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `header_id` bigint NOT NULL,
  `line_no` int NOT NULL DEFAULT '1',
  `cost_center_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `allocation_basis` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'machine_hours' COMMENT 'machine_hours/labor_hours/direct_labor_cost',
  `basis_qty_per_unit` decimal(18,6) NOT NULL DEFAULT '0.000000' COMMENT '配賦基準数量/単位',
  `overhead_rate` decimal(18,6) NOT NULL DEFAULT '0.000000' COMMENT '間接費率',
  `amount` decimal(18,4) NOT NULL DEFAULT '0.0000',
  PRIMARY KEY (`id`),
  KEY `idx_psol_header` (`header_id`),
  CONSTRAINT `fk_psol_header` FOREIGN KEY (`header_id`) REFERENCES `product_standard_costs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価 間接費明細';

SET FOREIGN_KEY_CHECKS = 1;
