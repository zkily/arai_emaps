-- TRIGGER (outsourcing_plating_receivings): trg_plating_receiving_after_insert
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_plating_receiving_after_insert`;

DELIMITER $$
CREATE TRIGGER `trg_plating_receiving_after_insert` AFTER INSERT ON `outsourcing_plating_receivings` FOR EACH ROW BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_plating_receivings WHERE order_id = NEW.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_plating_orders WHERE id = NEW.order_id LIMIT 1;

    UPDATE outsourcing_plating_orders
    SET received_qty = received_qty + COALESCE(NEW.good_qty, 0),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty + COALESCE(NEW.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = NEW.order_id;

    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        UPDATE outsourcing_plating_stock
        SET received_qty = received_qty + NEW.good_qty,
            last_receive_date = NEW.receiving_date
        WHERE product_cd = NEW.product_cd
          AND supplier_cd = NEW.supplier_cd
        LIMIT 1;

        IF ROW_COUNT() = 0 THEN
            INSERT INTO outsourcing_plating_stock
                (product_cd, product_name, supplier_cd, plating_type, received_qty, last_receive_date)
            VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.plating_type, NEW.good_qty, NEW.receiving_date);
        END IF;
    END IF;

    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date, 'receive', 'plating',
            NEW.product_cd, NEW.product_name, NEW.supplier_cd,
            NEW.receiving_no, NEW.good_qty, NEW.inspector
        );
    END IF;

    -- 良品数が 0 のときは実績行を保存しない
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT17' COLLATE utf8mb4_unicode_ci,
            '実績' COLLATE utf8mb4_unicode_ci,
            NEW.good_qty,
            '個' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            CONCAT(
                '外注メッキ受入: ', COALESCE(NEW.product_name, ''),
                ' | 受入番号: ', NEW.receiving_no,
                ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
                ' | 良品: ', NEW.good_qty,
                ' | 不良: ', COALESCE(NEW.defect_qty, 0),
                ' | 外注先: ', NEW.supplier_cd,
                IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
            ) COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_plating_receivings'
        );
    END IF;
    -- 不良数が 0 のときは不良行を保存しない
    IF COALESCE(NEW.defect_qty, 0) > 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT17' COLLATE utf8mb4_unicode_ci,
            '不良' COLLATE utf8mb4_unicode_ci,
            NEW.defect_qty,
            '個' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            CONCAT(
                '外注メッキ受入: ', COALESCE(NEW.product_name, ''),
                ' | 受入番号: ', NEW.receiving_no,
                ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
                ' | 良品: ', COALESCE(NEW.good_qty, 0),
                ' | 不良: ', NEW.defect_qty,
                ' | 外注先: ', NEW.supplier_cd,
                IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
            ) COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_plating_receivings'
        );
    END IF;
END$$
DELIMITER ;
