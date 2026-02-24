-- 外注溶接受入：任意項目変更時に stock_transaction_logs を同期（UPDATE または INSERT）、source_file を記録
-- 受入数・良品数・受入日・品名・検収者等を変更しても在庫履歴が必ず最新になる
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_welding_receiving_after_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_update` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE _remarks TEXT;

    -- 備考：受入数・良品・不良・検収者を含む（データ変更時に常に最新を反映）
    SET _remarks = CONCAT(
        '外注溶接受入: ', COALESCE(NEW.product_name, ''),
        ' | 受入番号: ', NEW.receiving_no,
        ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
        ' | 良品: ', COALESCE(NEW.good_qty, 0),
        ' | 不良: ', COALESCE(NEW.defect_qty, 0),
        ' | 外注先: ', NEW.supplier_cd,
        IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
    );

    -- 既存行があれば常に UPDATE（受入データのどの変更でも在庫履歴を同期）
    UPDATE stock_transaction_logs SET
        target_cd = NEW.product_cd,
        location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        process_cd = 'KT16' COLLATE utf8mb4_unicode_ci,
        transaction_type = '実績' COLLATE utf8mb4_unicode_ci,
        quantity = COALESCE(NEW.receiving_qty, 0),
        unit = '本' COLLATE utf8mb4_unicode_ci,
        transaction_time = CAST(NEW.receiving_date AS DATETIME),
        remarks = _remarks COLLATE utf8mb4_unicode_ci,
        unit_price = 0,
        source_file = 'outsourcing_welding_receivings'
    WHERE notes = NEW.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci;

    -- 行が無く受入数>0 のときのみ INSERT（初回受入や後から追加された受入番号用）
    IF ROW_COUNT() = 0 AND COALESCE(NEW.receiving_qty, 0) > 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT16' COLLATE utf8mb4_unicode_ci,
            '実績' COLLATE utf8mb4_unicode_ci,
            COALESCE(NEW.receiving_qty, 0),
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
