-- print-record / 出荷番号単位の更新で shipping_items の行ロック範囲を限定する
SET NAMES utf8mb4;

SET @idx_exists := (
  SELECT COUNT(1)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'shipping_items'
    AND INDEX_NAME = 'idx_shipping_items_shipping_no'
);
SET @sql := IF(
  @idx_exists = 0,
  'CREATE INDEX `idx_shipping_items_shipping_no` ON `shipping_items` (`shipping_no`)',
  'SELECT ''Index idx_shipping_items_shipping_no already exists'' AS msg'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
