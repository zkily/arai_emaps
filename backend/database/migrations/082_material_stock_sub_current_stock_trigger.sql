-- material_stock_sub: current_stock を order_quantity - planned_usage に応じて自動設定
-- order_quantity - planned_usage > 0 → current_stock = 1
-- order_quantity - planned_usage = 0 → current_stock = 0
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_material_stock_sub_current_stock_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_material_stock_sub_current_stock_before_insert`
BEFORE INSERT ON `material_stock_sub`
FOR EACH ROW
BEGIN
  IF (COALESCE(NEW.order_quantity, 0) - COALESCE(NEW.planned_usage, 0)) > 0 THEN
    SET NEW.current_stock = 1;
  ELSE
    SET NEW.current_stock = 0;
  END IF;
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `tg_material_stock_sub_current_stock_before_update`;
delimiter ;;
CREATE TRIGGER `tg_material_stock_sub_current_stock_before_update`
BEFORE UPDATE ON `material_stock_sub`
FOR EACH ROW
BEGIN
  IF (COALESCE(NEW.order_quantity, 0) - COALESCE(NEW.planned_usage, 0)) > 0 THEN
    SET NEW.current_stock = 1;
  ELSE
    SET NEW.current_stock = 0;
  END IF;
END
;;
delimiter ;
