-- shipping_items の BEFORE INSERT/UPDATE が shipping_no_p を
-- CONCAT(shipping_no, '_', product_cd) に固定していたため、
-- 同一出荷番号・同一品番で製品タイプが違う行（量産品+代替品など）は
-- UNIQUE(shipping_no_p) 衝突で INSERT IGNORE され、出荷リスト/印刷に出なかった。
-- 量産品以外は suffix に製品タイプを付ける。

SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_shipping_items_before_insert`;
delimiter ;;
CREATE TRIGGER `trg_shipping_items_before_insert` BEFORE INSERT ON `shipping_items` FOR EACH ROW BEGIN
  IF NEW.product_type IS NULL OR TRIM(NEW.product_type) = '' OR NEW.product_type = '量産品' THEN
    SET NEW.shipping_no_p = CONCAT(NEW.shipping_no, '_', NEW.product_cd);
  ELSE
    SET NEW.shipping_no_p = CONCAT(NEW.shipping_no, '_', NEW.product_cd, '_', NEW.product_type);
  END IF;
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `trg_shipping_items_before_update`;
delimiter ;;
CREATE TRIGGER `trg_shipping_items_before_update` BEFORE UPDATE ON `shipping_items` FOR EACH ROW BEGIN
  IF NEW.product_type IS NULL OR TRIM(NEW.product_type) = '' OR NEW.product_type = '量産品' THEN
    SET NEW.shipping_no_p = CONCAT(NEW.shipping_no, '_', NEW.product_cd);
  ELSE
    SET NEW.shipping_no_p = CONCAT(NEW.shipping_no, '_', NEW.product_cd, '_', NEW.product_type);
  END IF;
END
;;
delimiter ;
