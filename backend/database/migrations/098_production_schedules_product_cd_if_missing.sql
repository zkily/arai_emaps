-- production_schedules に product_cd が無い環境向け（095 未適用時の 500 防止）
SET @dbname = DATABASE();
SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'production_schedules' AND COLUMN_NAME = 'product_cd'
);
SET @sql := IF(
  @exist = 0,
  'ALTER TABLE `production_schedules` ADD COLUMN `product_cd` VARCHAR(50) NULL DEFAULT NULL COMMENT ''製品コード'' AFTER `item_name`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'production_schedules' AND INDEX_NAME = 'idx_ps_product_cd'
);
SET @sql2 := IF(
  @idx = 0,
  'CREATE INDEX `idx_ps_product_cd` ON `production_schedules` (`product_cd`)',
  'SELECT 1'
);
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;
