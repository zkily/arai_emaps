-- 外注溶接受入トリガー整理・修正（1ファイルに集約）
-- 表定義は 040_outsourcing_tables を参照。本ファイルはトリガーのみ DROP/CREATE。
-- 修正内容: INSERT/UPDATE の状態は「受入数合计>=注文数」で受入完、welding_stock は NULL 安全。
-- stock_transaction_logs: 1受入あたり2行（実績=良品数・不良=不良数）、任意変更で更新。DELETE 時は該当2行を削除。
SET NAMES utf8mb4;

-- =============================================================================
-- 1. AFTER INSERT：新規受入時に注文入庫数・溶接品在庫・入出庫履歴を追加
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_welding_receiving_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_insert` AFTER INSERT ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
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
END
;;
delimiter ;

-- =============================================================================
-- 2. AFTER UPDATE（良品数変化）：注文入庫数・溶接品在庫・入出庫履歴を差分更新
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_welding_receiving_after_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_update` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
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
END
;;
delimiter ;

-- =============================================================================
-- 3. AFTER UPDATE（stock_transaction_logs 同期）：良品数・不良数を在庫履歴に反映（任意変更で更新）
--    実績行: quantity=良品数 / 不良行: quantity=不良数, transaction_type='不良'
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_welding_receiving_to_stock_logs_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_to_stock_logs_update` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE _remarks TEXT;

    SET _remarks = CONCAT(
        '外注溶接受入: ', COALESCE(NEW.product_name, ''),
        ' | 受入番号: ', NEW.receiving_no,
        ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
        ' | 良品: ', COALESCE(NEW.good_qty, 0),
        ' | 不良: ', COALESCE(NEW.defect_qty, 0),
        ' | 外注先: ', NEW.supplier_cd,
        IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
    );

    -- 良品行（操作種別=実績、quantity=良品数）
    UPDATE stock_transaction_logs SET
        target_cd = NEW.product_cd,
        location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        process_cd = 'KT16' COLLATE utf8mb4_unicode_ci,
        transaction_type = '実績' COLLATE utf8mb4_unicode_ci,
        quantity = COALESCE(NEW.good_qty, 0),
        unit = '本' COLLATE utf8mb4_unicode_ci,
        transaction_time = CAST(NEW.receiving_date AS DATETIME),
        remarks = _remarks COLLATE utf8mb4_unicode_ci,
        unit_price = 0,
        source_file = 'outsourcing_welding_receivings'
    WHERE notes = NEW.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci
      AND transaction_type = '実績' COLLATE utf8mb4_unicode_ci;

    IF ROW_COUNT() = 0 THEN
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
            _remarks COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_welding_receivings'
        );
    END IF;

    -- 不良行（操作種別=不良、quantity=不良数）
    UPDATE stock_transaction_logs SET
        target_cd = NEW.product_cd,
        location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        process_cd = 'KT16' COLLATE utf8mb4_unicode_ci,
        transaction_type = '不良' COLLATE utf8mb4_unicode_ci,
        quantity = COALESCE(NEW.defect_qty, 0),
        unit = '本' COLLATE utf8mb4_unicode_ci,
        transaction_time = CAST(NEW.receiving_date AS DATETIME),
        remarks = _remarks COLLATE utf8mb4_unicode_ci,
        unit_price = 0,
        source_file = 'outsourcing_welding_receivings'
    WHERE notes = NEW.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci
      AND transaction_type = '不良' COLLATE utf8mb4_unicode_ci;

    IF ROW_COUNT() = 0 THEN
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
            _remarks COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_welding_receivings'
        );
    END IF;
END
;;
delimiter ;

-- =============================================================================
-- 4. AFTER DELETE：受入削除時に注文・在庫・履歴を回退
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_welding_receiving_after_delete`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_delete` AFTER DELETE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    -- 削除後残りの受入数合计（当該行は既に削除済み）
    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_welding_receivings WHERE order_id = OLD.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = OLD.order_id LIMIT 1;

    UPDATE outsourcing_welding_orders
    SET received_qty = GREATEST(0, received_qty - COALESCE(OLD.good_qty, 0)),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty - COALESCE(OLD.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = OLD.order_id;

    IF COALESCE(OLD.good_qty, 0) > 0 THEN
        UPDATE outsourcing_welding_stock
        SET received_qty = GREATEST(0, received_qty - OLD.good_qty)
        WHERE product_cd = OLD.product_cd
          AND supplier_cd = OLD.supplier_cd
          AND (welding_type <=> OLD.welding_type)
        ORDER BY id
        LIMIT 1;

        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            OLD.receiving_date, 'receive', 'welding',
            OLD.product_cd, OLD.product_name, OLD.supplier_cd,
            OLD.receiving_no, -OLD.good_qty, OLD.inspector
        );
    END IF;

    -- stock_transaction_logs：当該受入の良品行・不良行を削除
    DELETE FROM stock_transaction_logs
    WHERE notes = OLD.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci
      AND source_file = 'outsourcing_welding_receivings';
END
;;
delimiter ;
