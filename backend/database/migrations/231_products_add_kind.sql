SET NAMES utf8mb4;

SET @col_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'products'
    AND COLUMN_NAME = 'kind'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE `products` ADD COLUMN `kind` varchar(50) NULL DEFAULT NULL COMMENT ''分類'' AFTER `category`',
  'SELECT ''Column kind already exists'' AS msg'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
