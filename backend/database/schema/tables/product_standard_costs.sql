-- TABLE: product_standard_costs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_standard_costs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `version_id` int NOT NULL COMMENT 'cost_standard_versions.id',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '品名（スナップショット）',
  `material_cost_std` decimal(18,4) NOT NULL DEFAULT '0.0000' COMMENT '直接材料標準（単位）',
  `labor_cost_std` decimal(18,4) NOT NULL DEFAULT '0.0000' COMMENT '直接労務標準（単位）',
  `overhead_cost_std` decimal(18,4) NOT NULL DEFAULT '0.0000' COMMENT '製造間接標準（単位）',
  `total_cost_std` decimal(18,4) NOT NULL DEFAULT '0.0000' COMMENT '標準原価合計（単位）',
  `currency` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'JPY',
  `source` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'manual' COMMENT 'manual/import/rollup',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_psc_ver_prod` (`version_id`,`product_cd`),
  KEY `idx_psc_product` (`product_cd`),
  CONSTRAINT `fk_psc_version` FOREIGN KEY (`version_id`) REFERENCES `cost_standard_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品標準原価ヘッダ';

SET FOREIGN_KEY_CHECKS = 1;
