-- TABLE: stock_materials
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `stock_materials` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '在庫材料ID',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料名称',
  `manufacture_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '制造编号',
  `quantity` int NOT NULL DEFAULT '0' COMMENT '库存数量',
  `log_date` date NOT NULL COMMENT '日志日期',
  `supplier` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '供应商',
  `material_quality` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '材料质量',
  `is_used` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否已使用(0=未使用,1=已使用)',
  `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_material_name` (`material_name`),
  KEY `idx_manufacture_no` (`manufacture_no`),
  KEY `idx_log_date` (`log_date`),
  KEY `idx_supplier` (`supplier`),
  KEY `idx_is_used` (`is_used`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='在庫材料管理表';

SET FOREIGN_KEY_CHECKS = 1;
