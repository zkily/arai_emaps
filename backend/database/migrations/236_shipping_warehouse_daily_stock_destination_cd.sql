-- ================================================================
-- shipping_warehouse_daily_stock に destination_cd（納入先CD）を追加し、
-- UNIQUE を (destination_cd, product_cd, work_date) に更新（旧235適用済みDB向け）
-- Version: 236
-- ================================================================

SET NAMES utf8mb4;

-- 1) destination_cd カラム（存在しなければ追加）
SET @col_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'shipping_warehouse_daily_stock'
    AND COLUMN_NAME = 'destination_cd'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE `shipping_warehouse_daily_stock` ADD COLUMN `destination_cd` varchar(50) NOT NULL DEFAULT '''' COMMENT ''納入先CD'' AFTER `product_name`',
  'SELECT ''Column destination_cd already exists'' AS msg'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2) 旧 UNIQUE(product_cd, work_date) のみの場合は DROP
SET @uk_col_count := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'shipping_warehouse_daily_stock'
    AND INDEX_NAME = 'uk_shipping_warehouse_daily_stock'
);

SET @ddl_drop := IF(
  @uk_col_count = 2,
  'ALTER TABLE `shipping_warehouse_daily_stock` DROP INDEX `uk_shipping_warehouse_daily_stock`',
  'SELECT ''Skip drop uk (not old 2-column index)'' AS msg'
);

PREPARE stmt2 FROM @ddl_drop;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- 3) UNIQUE が無ければ (destination_cd, product_cd, work_date) で作成
SET @uk_now := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'shipping_warehouse_daily_stock'
    AND INDEX_NAME = 'uk_shipping_warehouse_daily_stock'
);

SET @ddl_add_uk := IF(
  @uk_now = 0,
  'ALTER TABLE `shipping_warehouse_daily_stock` ADD UNIQUE KEY `uk_shipping_warehouse_daily_stock` (`destination_cd`, `product_cd`, `work_date`)',
  'SELECT ''UK uk_shipping_warehouse_daily_stock already exists'' AS msg'
);

PREPARE stmt3 FROM @ddl_add_uk;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;

-- 4) 納入先CD 検索用インデックス
SET @idx_exists := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'shipping_warehouse_daily_stock'
    AND INDEX_NAME = 'idx_shipping_warehouse_daily_stock_destination_cd'
);

SET @ddl_idx := IF(
  @idx_exists = 0,
  'CREATE INDEX `idx_shipping_warehouse_daily_stock_destination_cd` ON `shipping_warehouse_daily_stock` (`destination_cd`)',
  'SELECT ''Index idx_shipping_warehouse_daily_stock_destination_cd already exists'' AS msg'
);

PREPARE stmt4 FROM @ddl_idx;
EXECUTE stmt4;
DEALLOCATE PREPARE stmt4;
