-- TRIGGER (outsourcing_material_issues): trg_material_issue_after_update
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_material_issue_after_update`;

DELIMITER $$
CREATE TRIGGER `trg_material_issue_after_update` AFTER UPDATE ON `outsourcing_material_issues` FOR EACH ROW BEGIN
    IF NEW.status = 'issued' AND OLD.status = 'preparing' THEN
        INSERT INTO outsourcing_supplied_material_stock 
        (supplier_cd, material_cd, material_name, spec, unit, unit_weight, issued_qty, last_issue_date)
        VALUES (NEW.supplier_cd, NEW.material_cd, NEW.material_name, NEW.spec, NEW.unit, NEW.unit_weight, NEW.quantity, NEW.issue_date)
        ON DUPLICATE KEY UPDATE 
            issued_qty = issued_qty + NEW.quantity,
            last_issue_date = NEW.issue_date;
        INSERT INTO outsourcing_material_transactions 
        (transaction_date, transaction_type, supplier_cd, material_cd, material_name, related_no, quantity, operator)
        VALUES (NEW.issue_date, 'issue', NEW.supplier_cd, NEW.material_cd, NEW.material_name, NEW.issue_no, NEW.quantity, NEW.operator);
    END IF;
END$$
DELIMITER ;
