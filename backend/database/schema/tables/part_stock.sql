-- TABLE: part_stock
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `part_stock` (
  `id` int NOT NULL AUTO_INCREMENT,
  `part_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '部品CD',
  `part_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '部品名',
  `date` date NOT NULL DEFAULT '2025-01-01' COMMENT '日付',
  `initial_stock` int DEFAULT '0' COMMENT '初期在庫',
  `current_stock` int DEFAULT '0' COMMENT '現在在庫',
  `planned_usage` int DEFAULT '0' COMMENT '使用数',
  `manual_usage` int NOT NULL DEFAULT '0' COMMENT '手動使用数',
  `usage_plan_qty` int NOT NULL DEFAULT '0' COMMENT '部品使用計画数量',
  `stock_trend` int NOT NULL DEFAULT '0' COMMENT '在庫推移',
  `adjustment_quantity` int DEFAULT '0' COMMENT '調整数',
  `standard_spec` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '規格・分類',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '単位',
  `unit_price` decimal(15,2) DEFAULT '0.00' COMMENT '単価',
  `pieces_per_bundle` int DEFAULT '0' COMMENT '梱包単位数',
  `supplier_cd` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '仕入先CD',
  `supplier_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '仕入先名',
  `lead_time` int DEFAULT '0' COMMENT 'リードタイム(日)',
  `order_quantity` int DEFAULT '0' COMMENT '注文数',
  `order_bundle_quantity` int DEFAULT '0' COMMENT '注文細目数',
  `order_amount` decimal(15,2) DEFAULT '0.00' COMMENT '注文金額',
  `last_updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `remarks` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '備考',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_part_stock_cd_date` (`part_cd`,`date`),
  KEY `idx_part_stock_cd` (`part_cd`),
  KEY `idx_part_stock_supplier` (`supplier_cd`),
  KEY `idx_part_stock_current` (`current_stock`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部品在庫メイン';

SET FOREIGN_KEY_CHECKS = 1;
