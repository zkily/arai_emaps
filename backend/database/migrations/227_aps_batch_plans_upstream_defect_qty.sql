-- aps_batch_plans：前工程（切断 + 面取）不良合計をロット単位で保持し、成型ロット計画（planned_quantity）の上限に反映する。
SET NAMES utf8mb4;

SET @dbname = DATABASE();

SET @col_exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'aps_batch_plans' AND COLUMN_NAME = 'upstream_defect_qty'
);
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE `aps_batch_plans` ADD COLUMN `upstream_defect_qty` int NOT NULL DEFAULT 0 COMMENT ''前工程不良合計（cutting_management + chamfering_management、management_code 照合）'' AFTER `planned_quantity`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
