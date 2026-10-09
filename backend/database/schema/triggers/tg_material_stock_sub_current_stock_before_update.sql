-- TRIGGER (material_stock_sub): tg_material_stock_sub_current_stock_before_update
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_material_stock_sub_current_stock_before_update`;

DELIMITER $$
CREATE TRIGGER `tg_material_stock_sub_current_stock_before_update` BEFORE UPDATE ON `material_stock_sub` FOR EACH ROW BEGIN
  IF (COALESCE(NEW.order_quantity, 0) - COALESCE(NEW.planned_usage, 0)) > 0 THEN
    SET NEW.current_stock = 1;
  ELSE
    SET NEW.current_stock = 0;
  END IF;
END$$
DELIMITER ;
