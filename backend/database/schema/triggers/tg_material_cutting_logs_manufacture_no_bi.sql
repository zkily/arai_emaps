-- TRIGGER (material_cutting_logs): tg_material_cutting_logs_manufacture_no_bi
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_material_cutting_logs_manufacture_no_bi`;

DELIMITER $$
CREATE TRIGGER `tg_material_cutting_logs_manufacture_no_bi` BEFORE INSERT ON `material_cutting_logs` FOR EACH ROW BEGIN
    IF NEW.material_cd IS NULL OR TRIM(NEW.material_cd) = '' THEN
        SET NEW.manufacture_no = NULL;
    ELSEIF NEW.material_cd LIKE '%荒井%' THEN
        SET NEW.manufacture_no = CONCAT('A', LEFT(NEW.material_cd, 13));
    ELSEIF LEFT(LTRIM(NEW.material_cd), 1) = 'N' THEN
        SET NEW.manufacture_no = LEFT(NEW.material_cd, 8);
    ELSE
        SET NEW.manufacture_no = NEW.material_cd;
    END IF;
END$$
DELIMITER ;
