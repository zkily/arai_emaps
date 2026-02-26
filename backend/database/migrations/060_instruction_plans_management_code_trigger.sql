-- instruction_plans の management_code トリガーを指定ロジックに統一
-- 形式: 西暦下2桁 + 月2桁 + 製品CD + ライン末尾2文字 + 順位 + - + 生産ロット数 + - + ロットNo
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_generate_management_code`;
delimiter ;;
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
END
;;
delimiter ;
