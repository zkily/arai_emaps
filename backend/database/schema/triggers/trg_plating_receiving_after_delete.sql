-- TRIGGER (outsourcing_plating_receivings): trg_plating_receiving_after_delete
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_plating_receiving_after_delete`;

DELIMITER $$
CREATE TRIGGER `trg_plating_receiving_after_delete` AFTER DELETE ON `outsourcing_plating_receivings` FOR EACH ROW BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_plating_receivings WHERE order_id = OLD.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_plating_orders WHERE id = OLD.order_id LIMIT 1;

    UPDATE outsourcing_plating_orders
    SET received_qty = GREATEST(0, received_qty - COALESCE(OLD.good_qty, 0)),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty - COALESCE(OLD.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = OLD.order_id;

    IF COALESCE(OLD.good_qty, 0) > 0 THEN
        UPDATE outsourcing_plating_stock
        SET received_qty = GREATEST(0, received_qty - OLD.good_qty)
        WHERE product_cd = OLD.product_cd
          AND supplier_cd = OLD.supplier_cd
        ORDER BY id
        LIMIT 1;

        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            OLD.receiving_date, 'receive', 'plating',
            OLD.product_cd, OLD.product_name, OLD.supplier_cd,
            OLD.receiving_no, -OLD.good_qty, OLD.inspector
        );
    END IF;

    DELETE FROM stock_transaction_logs
    WHERE notes = OLD.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
      AND source_file = 'outsourcing_plating_receivings';
END$$
DELIMITER ;
