-- TRIGGER (outsourcing_welding_orders): trg_welding_order_after_update
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_welding_order_after_update`;

DELIMITER $$
CREATE TRIGGER `trg_welding_order_after_update` AFTER UPDATE ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
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
            order_no,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文（発注済）: ', NEW.product_name, ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_welding_orders'
        );
    ELSEIF NEW.status = 'ordered' AND (
        (OLD.quantity <> NEW.quantity) OR
        (OLD.unit_price <> NEW.unit_price) OR
        (OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL)) OR
        (OLD.product_cd <> NEW.product_cd)
    ) THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            order_no,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity - OLD.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文変更（発注済）: ', NEW.product_name,
                   IF(OLD.quantity <> NEW.quantity, CONCAT(' | 数量: ', OLD.quantity, '→', NEW.quantity), ''),
                   IF(OLD.unit_price <> NEW.unit_price, CONCAT(' | 単価: ', OLD.unit_price, '→', NEW.unit_price), ''),
                   IF(OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL), ' | 納期変更', ''),
                   ' | 外注先: ', NEW.supplier_cd
            ),
            'outsourcing_welding_orders'
        );
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
            order_no,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            OLD.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            -OLD.quantity,
            OLD.unit,
            OLD.order_date,
            OLD.order_no,
            CONCAT('外注溶接注文取消: ', OLD.product_name, ' | 注文番号: ', OLD.order_no,
                   ' | 状態: ', OLD.status, '→', NEW.status, ' | 外注先: ', OLD.supplier_cd),
            'outsourcing_welding_orders'
        );
    END IF;
END$$
DELIMITER ;
