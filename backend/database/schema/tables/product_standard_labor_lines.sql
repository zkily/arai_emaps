-- TABLE: product_standard_labor_lines
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_standard_labor_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `header_id` bigint NOT NULL,
  `line_no` int NOT NULL DEFAULT '1',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `process_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `std_hours` decimal(18,6) NOT NULL DEFAULT '0.000000' COMMENT '標準直接作業時間',
  `setup_hours` decimal(18,6) NOT NULL DEFAULT '0.000000' COMMENT '段取時間',
  `labor_rate_per_hour` decimal(18,6) NOT NULL DEFAULT '0.000000' COMMENT '標準賃率/時',
  `cost_center_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount` decimal(18,4) NOT NULL DEFAULT '0.0000',
  PRIMARY KEY (`id`),
  KEY `idx_psll_header` (`header_id`),
  CONSTRAINT `fk_psll_header` FOREIGN KEY (`header_id`) REFERENCES `product_standard_costs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価 労務明細';

SET FOREIGN_KEY_CHECKS = 1;
