-- order_daily → sales_order / sales_order_item 同期用（重複防止キー）
SET NAMES utf8mb4;

SET @col_so_ref := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order' AND COLUMN_NAME = 'source_ref'
);
SET @ddl_so_ref := IF(
  @col_so_ref = 0,
  'ALTER TABLE sales_order ADD COLUMN source_ref VARCHAR(100) NULL COMMENT ''同期元キー OD|納入先CD|出荷日''',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_so_ref;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_item_od := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order_item' AND COLUMN_NAME = 'source_order_daily_id'
);
SET @ddl_item_od := IF(
  @col_item_od = 0,
  'ALTER TABLE sales_order_item ADD COLUMN source_order_daily_id INT NULL COMMENT ''元 order_daily.id''',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_item_od;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_so_ref := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order' AND INDEX_NAME = 'ux_sales_order_source_ref'
);
SET @ddl_idx_so := IF(
  @idx_so_ref = 0,
  'CREATE UNIQUE INDEX ux_sales_order_source_ref ON sales_order (source_ref)',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_idx_so;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_item_od := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order_item' AND INDEX_NAME = 'ux_sales_order_item_order_daily'
);
SET @ddl_idx_item := IF(
  @idx_item_od = 0,
  'CREATE UNIQUE INDEX ux_sales_order_item_order_daily ON sales_order_item (source_order_daily_id)',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_idx_item;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
