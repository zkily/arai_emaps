-- 備品発注：納入日

SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS migrate_supply_po_delivery_date;
DELIMITER //
CREATE PROCEDURE migrate_supply_po_delivery_date()
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'supply_purchase_orders'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'supply_purchase_orders'
      AND COLUMN_NAME = 'delivery_date'
  ) THEN
    ALTER TABLE `supply_purchase_orders`
      ADD COLUMN `delivery_date` date NULL DEFAULT NULL COMMENT '納入日' AFTER `order_date`;
  END IF;
END//
DELIMITER ;

CALL migrate_supply_po_delivery_date();
DROP PROCEDURE IF EXISTS migrate_supply_po_delivery_date;
