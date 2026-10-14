-- 補給品 出荷予定：手動で出荷済にできるフラグ（予定日は日受注から取得）
SET NAMES utf8mb4;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'supply_part_shipment_plans'
    AND COLUMN_NAME = 'is_shipped'
);
SET @sql = IF(
  @col_exists = 0,
  'ALTER TABLE `supply_part_shipment_plans` ADD COLUMN `is_shipped` tinyint(1) NOT NULL DEFAULT 0 COMMENT ''手動出荷済'' AFTER `planned_date`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
