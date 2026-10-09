-- TABLE: outsourcing_welding_stock
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `outsourcing_welding_stock` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品名',
  `supplier_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `welding_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '溶接種類',
  `ordered_qty` int DEFAULT '0' COMMENT '発注累計数量',
  `received_qty` int DEFAULT '0' COMMENT '入庫累計数量',
  `used_qty` int DEFAULT '0' COMMENT '出庫累計数量',
  `stock_qty` int GENERATED ALWAYS AS ((`ordered_qty` - `used_qty`)) STORED COMMENT '現在庫数量',
  `pending_qty` int DEFAULT '0' COMMENT '入庫予定数量',
  `min_stock` int DEFAULT '0' COMMENT '最低在庫数',
  `last_receive_date` date DEFAULT NULL COMMENT '最終入庫日',
  `last_issue_date` date DEFAULT NULL COMMENT '最終出庫日',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_product_supplier_welding` (`product_cd`,`supplier_cd`,`welding_type`) USING BTREE,
  KEY `idx_product_cd` (`product_cd`) USING BTREE,
  KEY `idx_supplier_cd` (`supplier_cd`) USING BTREE,
  KEY `idx_welding_type` (`welding_type`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='外注溶接品在庫';

SET FOREIGN_KEY_CHECKS = 1;
