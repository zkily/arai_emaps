-- 補給品 出荷済時に作成した実出荷（transactions）への紐付け
SET NAMES utf8mb4;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'supply_part_shipment_plans'
    AND COLUMN_NAME = 'shipment_txn_id'
);
SET @sql = IF(
  @col_exists = 0,
  'ALTER TABLE `supply_part_shipment_plans` ADD COLUMN `shipment_txn_id` bigint NULL DEFAULT NULL COMMENT ''出荷済で作成した実出荷ID'' AFTER `is_shipped`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
