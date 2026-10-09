-- TRIGGER (shipping_items): trg_shipping_items_before_update
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_shipping_items_before_update`;

DELIMITER $$
CREATE TRIGGER `trg_shipping_items_before_update` BEFORE UPDATE ON `shipping_items` FOR EACH ROW BEGIN
  IF NEW.product_type IS NULL OR TRIM(NEW.product_type) = '' OR NEW.product_type = '量産品' THEN
    SET NEW.shipping_no_p = CONCAT(NEW.shipping_no, '_', NEW.product_cd);
  ELSE
    SET NEW.shipping_no_p = CONCAT(NEW.shipping_no, '_', NEW.product_cd, '_', NEW.product_type);
  END IF;
END$$
DELIMITER ;
