-- TRIGGER (outsourcing_plating_receivings): trg_plating_receiving_after_update
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_plating_receiving_after_update`;

DELIMITER $$
CREATE TRIGGER `trg_plating_receiving_after_update` AFTER UPDATE ON `outsourcing_plating_receivings` FOR EACH ROW BEGIN
    DECLARE total_good INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;
    DECLARE stock_received INT DEFAULT 0;

    -- 該当注文の受入良品合計で直接セット
    SELECT COALESCE(SUM(good_qty), 0) INTO total_good
    FROM outsourcing_plating_receivings WHERE order_id = NEW.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_plating_orders WHERE id = NEW.order_id LIMIT 1;

    UPDATE outsourcing_plating_orders
    SET received_qty = total_good,
        status = CASE
            WHEN total_good >= order_qty_val THEN 'completed'
            WHEN total_good > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = NEW.order_id;

    -- 該当 product_cd + supplier_cd の受入良品合計で直接セット
    SELECT COALESCE(SUM(good_qty), 0) INTO stock_received
    FROM outsourcing_plating_receivings
    WHERE product_cd = NEW.product_cd AND supplier_cd = NEW.supplier_cd;

    UPDATE outsourcing_plating_stock
    SET received_qty = stock_received,
        last_receive_date = NEW.receiving_date
    WHERE product_cd = NEW.product_cd
      AND supplier_cd = NEW.supplier_cd
    LIMIT 1;

    IF ROW_COUNT() = 0 AND stock_received > 0 THEN
        INSERT INTO outsourcing_plating_stock
            (product_cd, product_name, supplier_cd, plating_type, received_qty, last_receive_date)
        VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.plating_type, stock_received, NEW.receiving_date);
    END IF;

    INSERT INTO outsourcing_stock_transactions
        (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
    VALUES (
        NEW.receiving_date, 'receive', 'plating',
        NEW.product_cd, NEW.product_name, NEW.supplier_cd,
        NEW.receiving_no, COALESCE(NEW.good_qty, 0) - COALESCE(OLD.good_qty, 0), NEW.inspector
    );
END$$
DELIMITER ;
