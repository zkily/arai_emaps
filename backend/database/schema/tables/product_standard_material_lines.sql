-- TABLE: product_standard_material_lines
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_standard_material_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `header_id` bigint NOT NULL COMMENT 'product_standard_costs.id',
  `line_no` int NOT NULL DEFAULT '1',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `material_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `qty_per_unit` decimal(18,6) NOT NULL DEFAULT '0.000000' COMMENT '単位製品当たり数量',
  `scrap_pct` decimal(9,4) NOT NULL DEFAULT '0.0000' COMMENT 'スクラップ率%',
  `standard_unit_price` decimal(18,6) NOT NULL DEFAULT '0.000000' COMMENT '標準単価',
  `amount` decimal(18,4) NOT NULL DEFAULT '0.0000' COMMENT '金額',
  `bom_line_id` int DEFAULT NULL COMMENT '参照BOM行',
  PRIMARY KEY (`id`),
  KEY `idx_psml_header` (`header_id`),
  CONSTRAINT `fk_psml_header` FOREIGN KEY (`header_id`) REFERENCES `product_standard_costs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価 材料明細';

SET FOREIGN_KEY_CHECKS = 1;
