-- 補給品化の移行トリガー（量産終了 / 顧客指定）と理由
SET NAMES utf8mb4;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'supply_part_stocks'
    AND COLUMN_NAME = 'migration_trigger'
);
SET @sql = IF(
  @col_exists = 0,
  'ALTER TABLE `supply_part_stocks` ADD COLUMN `migration_trigger` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT ''移行トリガー（mass_end/customer_spec）'' AFTER `source`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'supply_part_stocks'
    AND COLUMN_NAME = 'migration_reason'
);
SET @sql = IF(
  @col_exists = 0,
  'ALTER TABLE `supply_part_stocks` ADD COLUMN `migration_reason` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT ''移行理由'' AFTER `migration_trigger`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
