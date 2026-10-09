-- TRIGGER (outsourcing_plating_receivings): trg_plating_receiving_to_stock_logs_update
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_plating_receiving_to_stock_logs_update`;

DELIMITER $$
CREATE TRIGGER `trg_plating_receiving_to_stock_logs_update` AFTER UPDATE ON `outsourcing_plating_receivings` FOR EACH ROW BEGIN
    DECLARE _remarks TEXT;

    SET _remarks = CONCAT(
        '外注メッキ受入: ', COALESCE(NEW.product_name, ''),
        ' | 受入番号: ', NEW.receiving_no,
        ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
        ' | 良品: ', COALESCE(NEW.good_qty, 0),
        ' | 不良: ', COALESCE(NEW.defect_qty, 0),
        ' | 外注先: ', NEW.supplier_cd,
        IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
    );

    -- 良品行（実績）：良品数>0 のときのみ更新または挿入、0 のときは削除
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        UPDATE stock_transaction_logs SET
            target_cd = NEW.product_cd,
            location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            process_cd = 'KT17' COLLATE utf8mb4_unicode_ci,
            transaction_type = '実績' COLLATE utf8mb4_unicode_ci,
            quantity = NEW.good_qty,
            unit = '個' COLLATE utf8mb4_unicode_ci,
            transaction_time = CAST(NEW.receiving_date AS DATETIME),
            remarks = _remarks COLLATE utf8mb4_unicode_ci,
            unit_price = 0,
            source_file = 'outsourcing_plating_receivings'
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '実績' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';

        IF ROW_COUNT() = 0 THEN
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
                _remarks COLLATE utf8mb4_unicode_ci,
                0,
                'outsourcing_plating_receivings'
            );
        END IF;
    ELSE
        DELETE FROM stock_transaction_logs
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '実績' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';
    END IF;

    -- 不良行（不良）：不良数>0 のときのみ更新または挿入、0 のときは削除
    IF COALESCE(NEW.defect_qty, 0) > 0 THEN
        UPDATE stock_transaction_logs SET
            target_cd = NEW.product_cd,
            location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            process_cd = 'KT17' COLLATE utf8mb4_unicode_ci,
            transaction_type = '不良' COLLATE utf8mb4_unicode_ci,
            quantity = NEW.defect_qty,
            unit = '個' COLLATE utf8mb4_unicode_ci,
            transaction_time = CAST(NEW.receiving_date AS DATETIME),
            remarks = _remarks COLLATE utf8mb4_unicode_ci,
            unit_price = 0,
            source_file = 'outsourcing_plating_receivings'
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '不良' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';

        IF ROW_COUNT() = 0 THEN
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
                _remarks COLLATE utf8mb4_unicode_ci,
                0,
                'outsourcing_plating_receivings'
            );
        END IF;
    ELSE
        DELETE FROM stock_transaction_logs
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '不良' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';
    END IF;
END$$
DELIMITER ;
