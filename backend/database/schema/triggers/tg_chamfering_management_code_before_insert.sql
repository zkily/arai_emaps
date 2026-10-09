-- TRIGGER (chamfering_management): tg_chamfering_management_code_before_insert
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_chamfering_management_code_before_insert`;

DELIMITER $$
CREATE TRIGGER `tg_chamfering_management_code_before_insert` BEFORE INSERT ON `chamfering_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.production_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END$$
DELIMITER ;
