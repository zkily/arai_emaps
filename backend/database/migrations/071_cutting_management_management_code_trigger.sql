-- cutting_management の management_code を INSERT/UPDATE 時に自動設定（instruction_plans と同形式）
-- 形式: 西暦下2桁 + 月2桁 + 製品CD + ライン末尾2文字 + 順位(priority_order) + - + 生産ロット数 + - + ロットNo
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_cutting_management_code_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_cutting_management_code_before_insert` BEFORE INSERT ON `cutting_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `tg_cutting_management_code_before_update`;
delimiter ;;
CREATE TRIGGER `tg_cutting_management_code_before_update` BEFORE UPDATE ON `cutting_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;
