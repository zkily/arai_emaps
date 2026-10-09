-- TABLE: cost_period_product_costs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `cost_period_product_costs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `period_id` int NOT NULL,
  `version_id` int DEFAULT NULL COMMENT '標準計算に用いたバージョン（NULL=自動選択）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `finished_good_qty` decimal(18,4) NOT NULL DEFAULT '0.0000' COMMENT '完成品数量',
  `wip_equivalent_qty` decimal(18,4) NOT NULL DEFAULT '0.0000' COMMENT '仕掛約当数量',
  `actual_material_cost` decimal(18,2) DEFAULT NULL COMMENT '実際材料費（当期）',
  `actual_labor_cost` decimal(18,2) DEFAULT NULL COMMENT '実際労務費',
  `actual_overhead_cost` decimal(18,2) DEFAULT NULL COMMENT '実際間接費',
  `standard_material_allowed` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '標準許容 材料',
  `standard_labor_allowed` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '標準許容 労務',
  `standard_overhead_allowed` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '標準許容 間接',
  `variance_material_price` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '材料価格差異',
  `variance_material_qty` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '材料数量差異',
  `variance_labor_rate` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '賃率差異',
  `variance_labor_efficiency` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '作業時間差異',
  `variance_moh_budget` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '間接予算差異',
  `variance_moh_capacity` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '操業度差異',
  `variance_moh_efficiency` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '間接能率差異',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cpp_period_prod` (`period_id`,`product_cd`),
  KEY `idx_cpp_product` (`product_cd`),
  KEY `idx_cpp_version` (`version_id`),
  CONSTRAINT `fk_cpp_period` FOREIGN KEY (`period_id`) REFERENCES `cost_accounting_periods` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cpp_version` FOREIGN KEY (`version_id`) REFERENCES `cost_standard_versions` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='月次品目別 実績・標準許容・差異';

SET FOREIGN_KEY_CHECKS = 1;
