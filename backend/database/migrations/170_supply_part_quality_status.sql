-- 補給品 品質状態（良好 / 錆 / 汚れ / その他）
SET NAMES utf8mb4;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'supply_part_stocks'
    AND COLUMN_NAME = 'quality_status'
);
SET @sql = IF(
  @col_exists = 0,
  'ALTER TABLE `supply_part_stocks` ADD COLUMN `quality_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT ''良好'' COMMENT ''品質状態'' AFTER `next_production_qty`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
