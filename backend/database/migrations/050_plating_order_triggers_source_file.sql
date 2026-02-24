-- 外注メッキ注文触发器：向 stock_transaction_logs 写入时增加 order_no, source_file（与溶接 042/043 同逻辑）
-- process_cd: KT06 = 外注メッキ（database/api.py と一致）
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_plating_order_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_plating_order_after_insert` AFTER INSERT ON `outsourcing_plating_orders` FOR EACH ROW BEGIN
    IF NEW.status = 'ordered' THEN
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
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT06',
            '実績',
            NEW.quantity,
            COALESCE(NEW.unit, '本'),
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注メッキ注文: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_plating_orders'
        );
    END IF;
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `trg_plating_order_after_update`;
delimiter ;;
CREATE TRIGGER `trg_plating_order_after_update` AFTER UPDATE ON `outsourcing_plating_orders` FOR EACH ROW BEGIN
    IF (OLD.status <> 'ordered' OR OLD.status IS NULL) AND NEW.status = 'ordered' THEN
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
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT06',
            '実績',
            NEW.quantity,
            COALESCE(NEW.unit, '本'),
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注メッキ注文（発注済）: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_plating_orders'
        );
    ELSEIF NEW.status = 'ordered' AND (
        (OLD.quantity <> NEW.quantity) OR
        (OLD.unit_price <> NEW.unit_price) OR
        (OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL)) OR
        (OLD.product_cd <> NEW.product_cd)
    ) THEN
        -- 直接用更新数量方式（加减しない）：既存行を quantity=NEW.quantity で更新、なければ INSERT
        -- 照合順序の混在エラー回避: notes と NEW.order_no を utf8mb4_unicode_ci で比較
        UPDATE stock_transaction_logs SET
            target_cd = NEW.product_cd,
            location_cd = '外注倉庫',
            process_cd = 'KT06',
            quantity = NEW.quantity,
            unit = COALESCE(NEW.unit, '個'),
            transaction_time = NEW.order_date,
            notes = CONVERT(NEW.order_no USING utf8mb4) COLLATE utf8mb4_unicode_ci,
            remarks = CONCAT('外注メッキ注文（発注済）: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
            source_file = 'outsourcing_plating_orders'
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.order_no COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_orders'
          AND process_cd = 'KT06'
          AND transaction_type = '実績';

        IF ROW_COUNT() = 0 THEN
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
                source_file
            ) VALUES (
                '仕掛品',
                NEW.product_cd,
                '外注倉庫',
                'KT06',
                '実績',
                NEW.quantity,
                COALESCE(NEW.unit, '個'),
                NEW.order_date,
                NEW.order_no,
                CONCAT('外注メッキ注文（発注済）: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
                'outsourcing_plating_orders'
            );
        END IF;
    ELSEIF OLD.status = 'ordered' AND NEW.status = 'cancelled' THEN
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
            source_file
        ) VALUES (
            '仕掛品',
            OLD.product_cd,
            '外注倉庫',
            'KT06',
            '実績',
            -OLD.quantity,
            COALESCE(OLD.unit, '個'),
            OLD.order_date,
            OLD.order_no,
            CONCAT('外注メッキ注文取消: ', COALESCE(OLD.product_name, ''), ' | 注文番号: ', OLD.order_no,
                   ' | 状態: ', OLD.status, '→', NEW.status, ' | 外注先: ', OLD.supplier_cd),
            'outsourcing_plating_orders'
        );
    END IF;
END
;;
delimiter ;
