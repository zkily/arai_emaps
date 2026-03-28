-- 201: ロット計画本数のスナップショット（計画一覧由来。成型実績・再排産で planned_quantity が変わっても表示用に保持）
SET NAMES utf8mb4;

SET @dbname = DATABASE();
SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'aps_batch_plans' AND COLUMN_NAME = 'original_planned_quantity'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `aps_batch_plans` ADD COLUMN `original_planned_quantity` INT NULL DEFAULT NULL COMMENT ''計画一覧確定時のロット本数（生産進捗の計画数表示用）'' AFTER `planned_quantity`',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE `aps_batch_plans`
SET `original_planned_quantity` = `planned_quantity`
WHERE `original_planned_quantity` IS NULL;
