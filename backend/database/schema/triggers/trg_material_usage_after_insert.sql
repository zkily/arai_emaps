-- TRIGGER (outsourcing_material_usages): trg_material_usage_after_insert
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_material_usage_after_insert`;

DELIMITER $$
CREATE TRIGGER `trg_material_usage_after_insert` AFTER INSERT ON `outsourcing_material_usages` FOR EACH ROW BEGIN
    UPDATE outsourcing_supplied_material_stock 
    SET used_qty = used_qty + NEW.usage_qty,
        last_usage_date = NEW.usage_date
    WHERE supplier_cd = NEW.supplier_cd AND material_cd = NEW.material_cd;
    INSERT INTO outsourcing_material_transactions 
    (transaction_date, transaction_type, supplier_cd, material_cd, material_name, related_no, quantity, operator)
    VALUES (NEW.usage_date, 'usage', NEW.supplier_cd, NEW.material_cd, NEW.material_name, NEW.usage_no, NEW.usage_qty, NEW.reporter);
END$$
DELIMITER ;
