-- material_stock に adjustment_quantity が無い環境向けにカラムを追加（074 と揃える）
-- 既に存在する場合はスキップする

SET @dbname = DATABASE();
SET @tablename = 'material_stock';
SET @columnname = 'adjustment_quantity';
SET @prepared = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname);

SET @sql = IF(@prepared = 0,
  'ALTER TABLE `material_stock` ADD COLUMN `adjustment_quantity` int NULL DEFAULT 0 COMMENT ''調整数'' AFTER `planned_usage`',
  'SELECT 1');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
