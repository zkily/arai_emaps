-- TABLE: product_bom_lines
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_bom_lines` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `header_id` int NOT NULL COMMENT 'ヘッダID',
  `parent_line_id` int DEFAULT NULL COMMENT '親行ID (多階層)',
  `line_no` int NOT NULL DEFAULT '10' COMMENT '行番号',
  `component_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'material' COMMENT '子品目種別 (material/purchased/subassy/phantom)',
  `component_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '子品目の製品CD',
  `component_material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '子品目の材料CD',
  `qty_per` decimal(12,6) NOT NULL DEFAULT '1.000000' COMMENT '親1基準あたり所要量',
  `uom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '個' COMMENT '単位',
  `scrap_rate` decimal(5,2) DEFAULT '0.00' COMMENT 'スクラップ率 (%)',
  `consume_process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '投入工程CD',
  `consume_step_no` int DEFAULT NULL COMMENT '投入ステップ番号',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '備考',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_bom_line_header` (`header_id`),
  KEY `idx_bom_line_parent_line` (`parent_line_id`),
  KEY `idx_bom_line_component` (`component_product_cd`),
  CONSTRAINT `fk_bom_line_header` FOREIGN KEY (`header_id`) REFERENCES `product_bom_headers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_bom_line_parent` FOREIGN KEY (`parent_line_id`) REFERENCES `product_bom_lines` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='明細BOM行';

SET FOREIGN_KEY_CHECKS = 1;
