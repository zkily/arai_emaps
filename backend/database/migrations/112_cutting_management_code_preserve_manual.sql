-- 切断指示編集で管理コードを手修正できるよう、
-- BEFORE UPDATE トリガーは「空欄 or 未変更」のときだけ自動再計算する。
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_cutting_management_code_before_update`;
delimiter ;;
CREATE TRIGGER `tg_cutting_management_code_before_update` BEFORE UPDATE ON `cutting_management` FOR EACH ROW BEGIN
    IF NEW.management_code IS NULL OR TRIM(NEW.management_code) = ''
       OR (NEW.management_code <=> OLD.management_code) THEN
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
    END IF;
END
;;
delimiter ;
