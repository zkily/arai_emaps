-- TRIGGER (instruction_plans): tg_generate_management_code
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_generate_management_code`;

DELIMITER $$
CREATE TRIGGER `tg_generate_management_code` BEFORE INSERT ON `instruction_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        NEW.product_cd,
        RIGHT(NEW.production_line, 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END$$
DELIMITER ;
