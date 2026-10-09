-- TRIGGER (outsourcing_welding_receivings): trg_welding_receiving_after_update
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_welding_receiving_after_update`;

DELIMITER $$
CREATE TRIGGER `trg_welding_receiving_after_update` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW BEGIN
    DECLARE good_qty_diff INT DEFAULT 0;
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    SET good_qty_diff = COALESCE(NEW.good_qty, 0) - COALESCE(OLD.good_qty, 0);

    IF good_qty_diff != 0 THEN
        SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
        FROM outsourcing_welding_receivings WHERE order_id = NEW.order_id;
        SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = NEW.order_id LIMIT 1;

        UPDATE outsourcing_welding_orders
        SET received_qty = GREATEST(0, received_qty + good_qty_diff),
            status = CASE
                WHEN total_received >= order_qty_val THEN 'completed'
                WHEN received_qty + good_qty_diff > 0 THEN 'partial'
                ELSE 'ordered'
            END
        WHERE id = NEW.order_id;

        IF good_qty_diff > 0 THEN
            UPDATE outsourcing_welding_stock
            SET received_qty = received_qty + good_qty_diff,
                last_receive_date = NEW.receiving_date
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type <=> NEW.welding_type)
            LIMIT 1;
            IF ROW_COUNT() = 0 THEN
                INSERT INTO outsourcing_welding_stock
                    (product_cd, product_name, supplier_cd, welding_type, received_qty, last_receive_date)
                VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.welding_type, good_qty_diff, NEW.receiving_date);
            END IF;
        ELSE
            UPDATE outsourcing_welding_stock
            SET received_qty = GREATEST(0, received_qty + good_qty_diff)
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type <=> NEW.welding_type)
            ORDER BY id
            LIMIT 1;
        END IF;

        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date, 'receive', 'welding',
            NEW.product_cd, NEW.product_name, NEW.supplier_cd,
            NEW.receiving_no, good_qty_diff, NEW.inspector
        );
    END IF;
END$$
DELIMITER ;
