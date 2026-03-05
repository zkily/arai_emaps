-- chamfering_plans の management_code を INSERT/UPDATE 時に自動設定（instruction_plans と同形式）
-- 形式: 西暦下2桁 + 月2桁 + 製品CD + ライン末尾2文字 + 順位(production_order) + - + 生産ロット数 + - + ロットNo
-- management_code 変更時に cd（管理コード後5位）も同一トリガー内で更新するため、063 の cd 専用トリガーを削除
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `chamfering_plans_cd_before_insert`;
DROP TRIGGER IF EXISTS `chamfering_plans_cd_before_update`;

DROP TRIGGER IF EXISTS `tg_chamfering_plans_code_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_plans_code_before_insert` BEFORE INSERT ON `chamfering_plans` FOR EACH ROW BEGIN
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
    SET NEW.cd = IF(TRIM(COALESCE(NEW.management_code, '')) != '', RIGHT(NEW.management_code, 5), NULL);
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `tg_chamfering_plans_code_before_update`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_plans_code_before_update` BEFORE UPDATE ON `chamfering_plans` FOR EACH ROW BEGIN
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
    SET NEW.cd = IF(TRIM(COALESCE(NEW.management_code, '')) != '', RIGHT(NEW.management_code, 5), NULL);
END
;;
delimiter ;
