-- TABLE: outsourcing_supplied_material_stock
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `outsourcing_supplied_material_stock` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料コード',
  `material_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '材料名',
  `spec` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '規格',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '個' COMMENT '単位',
  `unit_weight` decimal(10,4) DEFAULT '0.0000' COMMENT '単重（kg）',
  `issued_qty` decimal(12,3) DEFAULT '0.000' COMMENT '支給累計数量',
  `used_qty` decimal(12,3) DEFAULT '0.000' COMMENT '使用累計数量',
  `stock_qty` decimal(12,3) GENERATED ALWAYS AS ((`issued_qty` - `used_qty`)) STORED COMMENT '現在庫数量',
  `min_stock` decimal(12,3) DEFAULT '0.000' COMMENT '最低在庫数',
  `last_issue_date` date DEFAULT NULL COMMENT '最終支給日',
  `last_usage_date` date DEFAULT NULL COMMENT '最終使用日',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_supplier_material` (`supplier_cd`,`material_cd`) USING BTREE,
  KEY `idx_supplier_cd` (`supplier_cd`) USING BTREE,
  KEY `idx_material_cd` (`material_cd`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='外注先支給材料在庫';

SET FOREIGN_KEY_CHECKS = 1;
