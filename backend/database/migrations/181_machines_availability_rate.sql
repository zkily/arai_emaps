-- 設備マスタ：可動率（%・小数第1位）
SET NAMES utf8mb4;

SET @col_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'machines'
    AND COLUMN_NAME = 'availability_rate'
);

SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `machines` ADD COLUMN `availability_rate` decimal(4, 1) NULL DEFAULT 100.0 COMMENT ''可動率（%）'' AFTER `efficiency`',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
