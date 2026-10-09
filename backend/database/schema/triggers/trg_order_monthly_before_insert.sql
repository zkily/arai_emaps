-- TRIGGER (order_monthly): trg_order_monthly_before_insert
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_order_monthly_before_insert`;

DELIMITER $$
CREATE TRIGGER `trg_order_monthly_before_insert` BEFORE INSERT ON `order_monthly` FOR EACH ROW BEGIN
  DECLARE typeSuffix CHAR(1);

  SET typeSuffix = CASE NEW.product_type
    WHEN '試作品' THEN '1'
    WHEN '別注品' THEN '2'
    WHEN '補給品' THEN '3'
    WHEN 'サンプル品' THEN '4'
    WHEN '代替品' THEN '5'
    WHEN '返却品' THEN '6'
    WHEN 'その他' THEN '7'
    ELSE '0'
  END;

  SET NEW.order_id = CONCAT(
    NEW.year,
    LPAD(NEW.month, 2, '0'),
    NEW.destination_cd,
    NEW.product_cd,
    typeSuffix
  );
END$$
DELIMITER ;
