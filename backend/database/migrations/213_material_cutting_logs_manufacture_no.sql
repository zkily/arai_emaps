-- material_cutting_logs: manufacture_no（材料コードからトリガーで自動設定）
-- ルール:
--   1) material_cd に「荒井」を含む → 'A' + material_cd の先頭13文字
--   2) material_cd が N で始まる（先頭空白除く）→ material_cd の先頭8文字
--   3) それ以外 → material_cd 全文
SET NAMES utf8mb4;

ALTER TABLE `material_cutting_logs`
    ADD COLUMN `manufacture_no` VARCHAR(255) NULL DEFAULT NULL COMMENT '製造番号（材料コードより自動算出）' AFTER `material_cd`;

DROP TRIGGER IF EXISTS `tg_material_cutting_logs_manufacture_no_bi`;
delimiter ;;
CREATE TRIGGER `tg_material_cutting_logs_manufacture_no_bi` BEFORE INSERT ON `material_cutting_logs` FOR EACH ROW
BEGIN
    IF NEW.material_cd IS NULL OR TRIM(NEW.material_cd) = '' THEN
        SET NEW.manufacture_no = NULL;
    ELSEIF NEW.material_cd LIKE '%荒井%' THEN
        SET NEW.manufacture_no = CONCAT('A', LEFT(NEW.material_cd, 13));
    ELSEIF LEFT(LTRIM(NEW.material_cd), 1) = 'N' THEN
        SET NEW.manufacture_no = LEFT(NEW.material_cd, 8);
    ELSE
        SET NEW.manufacture_no = NEW.material_cd;
    END IF;
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `tg_material_cutting_logs_manufacture_no_bu`;
delimiter ;;
CREATE TRIGGER `tg_material_cutting_logs_manufacture_no_bu` BEFORE UPDATE ON `material_cutting_logs` FOR EACH ROW
BEGIN
    IF NEW.material_cd IS NULL OR TRIM(NEW.material_cd) = '' THEN
        SET NEW.manufacture_no = NULL;
    ELSEIF NEW.material_cd LIKE '%荒井%' THEN
        SET NEW.manufacture_no = CONCAT('A', LEFT(NEW.material_cd, 13));
    ELSEIF LEFT(LTRIM(NEW.material_cd), 1) = 'N' THEN
        SET NEW.manufacture_no = LEFT(NEW.material_cd, 8);
    ELSE
        SET NEW.manufacture_no = NEW.material_cd;
    END IF;
END
;;
delimiter ;

-- 既存行のバックフィル
UPDATE `material_cutting_logs`
SET `manufacture_no` = CASE
    WHEN `material_cd` IS NULL OR TRIM(`material_cd`) = '' THEN NULL
    WHEN `material_cd` LIKE '%荒井%' THEN CONCAT('A', LEFT(`material_cd`, 13))
    WHEN LEFT(LTRIM(`material_cd`), 1) = 'N' THEN LEFT(`material_cd`, 8)
    ELSE `material_cd`
END;
