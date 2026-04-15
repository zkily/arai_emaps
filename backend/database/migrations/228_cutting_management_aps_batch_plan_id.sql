-- cutting_management に APS ロット安定キー（aps_batch_plans.id）を追加し、
-- 前工程不良集計・顺位変更後も instruction_plans / APS と追跡可能にする。
SET NAMES utf8mb4;

SET @dbname = DATABASE();

SET @col_exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'cutting_management' AND COLUMN_NAME = 'aps_batch_plan_id'
);
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE `cutting_management` ADD COLUMN `aps_batch_plan_id` int NULL DEFAULT NULL COMMENT ''APS ロット（aps_batch_plans.id）参照'' AFTER `management_code`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'cutting_management' AND INDEX_NAME = 'idx_cutting_aps_batch_plan_id'
);
SET @sql2 := IF(@idx_exists = 0,
  'CREATE INDEX `idx_cutting_aps_batch_plan_id` ON `cutting_management` (`aps_batch_plan_id`)',
  'SELECT 1');
PREPARE stmt2 FROM @sql2; EXECUTE stmt2; DEALLOCATE PREPARE stmt2;

-- FK（存在時のみ付与）
SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'cutting_management'
    AND CONSTRAINT_NAME = 'fk_cutting_management_aps_batch_plan'
);
SET @sql3 := IF(@fk_exists = 0,
  'ALTER TABLE `cutting_management` ADD CONSTRAINT `fk_cutting_management_aps_batch_plan` FOREIGN KEY (`aps_batch_plan_id`) REFERENCES `aps_batch_plans` (`id`) ON DELETE SET NULL ON UPDATE CASCADE',
  'SELECT 1');
PREPARE stmt3 FROM @sql3; EXECUTE stmt3; DEALLOCATE PREPARE stmt3;

-- 既存行のベストエフォート突合（品番・ロット・生産月）。複数 aps_batch_plans が一致する場合は MIN(id) を採用。
UPDATE `cutting_management` cm
INNER JOIN (
  SELECT MIN(`id`) AS `id`, `product_cd`, `lot_number`, `production_month`
  FROM `aps_batch_plans`
  GROUP BY `product_cd`, `lot_number`, `production_month`
) abp
  ON TRIM(COALESCE(cm.`product_cd`,'')) = TRIM(COALESCE(abp.`product_cd`,''))
 AND TRIM(COALESCE(cm.`lot_number`,'')) = TRIM(COALESCE(abp.`lot_number`,''))
 AND cm.`production_month` = abp.`production_month`
SET cm.`aps_batch_plan_id` = abp.`id`
WHERE cm.`aps_batch_plan_id` IS NULL;
