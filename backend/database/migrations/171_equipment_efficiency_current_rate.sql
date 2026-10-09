-- 設備能率：直近3ヶ月の生産性から算出した現在能率
SET NAMES utf8mb4;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'equipment_efficiency'
    AND COLUMN_NAME = 'current_efficiency_rate'
);
SET @sql = IF(
  @col_exists = 0,
  'ALTER TABLE `equipment_efficiency` ADD COLUMN `current_efficiency_rate` decimal(10, 1) NULL DEFAULT NULL COMMENT ''現在能率（直近3ヶ月の生産性×95%）'' AFTER `efficiency_rate`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'equipment_efficiency'
    AND COLUMN_NAME = 'current_efficiency_updated_at'
);
SET @sql = IF(
  @col_exists = 0,
  'ALTER TABLE `equipment_efficiency` ADD COLUMN `current_efficiency_updated_at` datetime NULL DEFAULT NULL COMMENT ''現在能率の更新日時'' AFTER `current_efficiency_rate`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
