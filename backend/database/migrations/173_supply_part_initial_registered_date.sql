-- 補給品 最初登録日（手動登録時に入力、後から修正可）
SET NAMES utf8mb4;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'supply_part_stocks'
    AND COLUMN_NAME = 'initial_registered_date'
);
SET @sql = IF(
  @col_exists = 0,
  'ALTER TABLE `supply_part_stocks` ADD COLUMN `initial_registered_date` date NULL DEFAULT NULL COMMENT ''最初登録日'' AFTER `migration_reason`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE `supply_part_stocks`
SET `initial_registered_date` = DATE(`created_at`)
WHERE `initial_registered_date` IS NULL AND `created_at` IS NOT NULL;

UPDATE `supply_part_stocks`
SET `initial_registered_date` = CURDATE()
WHERE `initial_registered_date` IS NULL;
