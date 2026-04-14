-- 部品購買・在庫：主表作成、廃止テーブル削除、既存 part_stock の列整合（224–228 を統合）
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 1) 部品在庫メイン（material_stock と同形・拡張）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `part_stock` (
  `id` int NOT NULL AUTO_INCREMENT,
  `part_cd` varchar(50) NOT NULL COMMENT '部品CD',
  `part_name` varchar(50) NOT NULL COMMENT '部品名',
  `date` date NOT NULL DEFAULT '2025-01-01' COMMENT '日付',
  `initial_stock` int DEFAULT 0 COMMENT '初期在庫',
  `current_stock` int DEFAULT 0 COMMENT '現在在庫',
  `planned_usage` int DEFAULT 0 COMMENT '使用数',
  `usage_plan_qty` int NOT NULL DEFAULT 0 COMMENT '部品使用計画数量',
  `stock_trend` int NOT NULL DEFAULT 0 COMMENT '在庫推移',
  `adjustment_quantity` int DEFAULT 0 COMMENT '調整数',
  `standard_spec` varchar(50) DEFAULT '' COMMENT '規格・分類',
  `unit` varchar(20) DEFAULT NULL COMMENT '単位',
  `unit_price` decimal(15,2) DEFAULT 0.00 COMMENT '単価',
  `pieces_per_bundle` int DEFAULT 0 COMMENT '梱包単位数',
  `supplier_cd` varchar(15) DEFAULT NULL COMMENT '仕入先CD',
  `supplier_name` varchar(50) DEFAULT NULL COMMENT '仕入先名',
  `lead_time` int DEFAULT 0 COMMENT 'リードタイム(日)',
  `order_quantity` int DEFAULT 0 COMMENT '注文数',
  `order_bundle_quantity` int DEFAULT 0 COMMENT '注文細目数',
  `order_amount` decimal(15,2) DEFAULT 0.00 COMMENT '注文金額',
  `last_updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `remarks` varchar(50) DEFAULT '' COMMENT '備考',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_part_stock_cd_date` (`part_cd`, `date`),
  KEY `idx_part_stock_cd` (`part_cd`),
  KEY `idx_part_stock_supplier` (`supplier_cd`),
  KEY `idx_part_stock_current` (`current_stock`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部品在庫メイン';

-- ---------------------------------------------------------------------------
-- 2) 廃止テーブル削除（主表 part_stock のみ運用）
-- ---------------------------------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `part_stock_sub`;
SET FOREIGN_KEY_CHECKS = 1;

DROP TABLE IF EXISTS `part_demand_daily`;

DROP TABLE IF EXISTS `part_logs`;
DROP TABLE IF EXISTS `part_inspection_master`;

-- ---------------------------------------------------------------------------
-- 3) 既存 DB の part_stock：列の追加・旧列削除（列の有無で分岐）
-- ---------------------------------------------------------------------------
SET @db = DATABASE();

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'usage_plan_qty'
);
SET @sql := IF(@exist = 0,
  'ALTER TABLE part_stock ADD COLUMN `usage_plan_qty` int NOT NULL DEFAULT 0 COMMENT ''部品使用計画数量'' AFTER `planned_usage`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'stock_trend'
);
SET @sql := IF(@exist = 0,
  'ALTER TABLE part_stock ADD COLUMN `stock_trend` int NOT NULL DEFAULT 0 COMMENT ''在庫推移'' AFTER `usage_plan_qty`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'safety_stock'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `safety_stock`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'long_weight'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `long_weight`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'max_stock'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `max_stock`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'bundle_quantity'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `bundle_quantity`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'bundle_weight'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `bundle_weight`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
