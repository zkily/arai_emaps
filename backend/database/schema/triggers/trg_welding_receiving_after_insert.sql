-- TRIGGER (outsourcing_welding_receivings): trg_welding_receiving_after_insert
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_welding_receiving_after_insert`;

DELIMITER $$
CREATE TRIGGER `trg_welding_receiving_after_insert` AFTER INSERT ON `outsourcing_welding_receivings` FOR EACH ROW BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    -- 注文：入庫数に良品数を加算、状態は受入数合计>=注文数で completed
    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_welding_receivings WHERE order_id = NEW.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = NEW.order_id LIMIT 1;

    UPDATE outsourcing_welding_orders
    SET received_qty = received_qty + COALESCE(NEW.good_qty, 0),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty + COALESCE(NEW.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = NEW.order_id;

    -- 溶接品在庫：良品>0 のときのみ。先 UPDATE、該当行がなければ INSERT（NULL welding_type 対応）
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        UPDATE outsourcing_welding_stock
        SET received_qty = received_qty + NEW.good_qty,
            last_receive_date = NEW.receiving_date
        WHERE product_cd = NEW.product_cd
          AND supplier_cd = NEW.supplier_cd
          AND (welding_type <=> NEW.welding_type)
        LIMIT 1;

        IF ROW_COUNT() = 0 THEN
            INSERT INTO outsourcing_welding_stock
                (product_cd, product_name, supplier_cd, welding_type, received_qty, last_receive_date)
            VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.welding_type, NEW.good_qty, NEW.receiving_date);
        END IF;
    END IF;

    -- 入出庫履歴：良品>0 のときのみ
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date, 'receive', 'welding',
            NEW.product_cd, NEW.product_name, NEW.supplier_cd,
            NEW.receiving_no, NEW.good_qty, NEW.inspector
        );
    END IF;

    -- stock_transaction_logs：良品行（実績）・不良行（不良）を登録
    INSERT INTO stock_transaction_logs (
        stock_type, target_cd, location_cd, process_cd, transaction_type,
        quantity, unit, transaction_time, notes, remarks, unit_price, source_file
    ) VALUES (
        '仕掛品' COLLATE utf8mb4_unicode_ci,
        NEW.product_cd,
        '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        'KT16' COLLATE utf8mb4_unicode_ci,
        '実績' COLLATE utf8mb4_unicode_ci,
        COALESCE(NEW.good_qty, 0),
        '本' COLLATE utf8mb4_unicode_ci,
        CAST(NEW.receiving_date AS DATETIME),
        NEW.receiving_no,
        CONCAT(
            '外注溶接受入: ', COALESCE(NEW.product_name, ''),
            ' | 受入番号: ', NEW.receiving_no,
            ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
            ' | 良品: ', COALESCE(NEW.good_qty, 0),
            ' | 不良: ', COALESCE(NEW.defect_qty, 0),
            ' | 外注先: ', NEW.supplier_cd,
            IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
        ) COLLATE utf8mb4_unicode_ci,
        0,
        'outsourcing_welding_receivings'
    );
    INSERT INTO stock_transaction_logs (
        stock_type, target_cd, location_cd, process_cd, transaction_type,
        quantity, unit, transaction_time, notes, remarks, unit_price, source_file
    ) VALUES (
        '仕掛品' COLLATE utf8mb4_unicode_ci,
        NEW.product_cd,
        '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        'KT16' COLLATE utf8mb4_unicode_ci,
        '不良' COLLATE utf8mb4_unicode_ci,
        COALESCE(NEW.defect_qty, 0),
        '本' COLLATE utf8mb4_unicode_ci,
        CAST(NEW.receiving_date AS DATETIME),
        NEW.receiving_no,
        CONCAT(
            '外注溶接受入: ', COALESCE(NEW.product_name, ''),
            ' | 受入番号: ', NEW.receiving_no,
            ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
            ' | 良品: ', COALESCE(NEW.good_qty, 0),
            ' | 不良: ', COALESCE(NEW.defect_qty, 0),
            ' | 外注先: ', NEW.supplier_cd,
            IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
        ) COLLATE utf8mb4_unicode_ci,
        0,
        'outsourcing_welding_receivings'
    );
END$$
DELIMITER ;
