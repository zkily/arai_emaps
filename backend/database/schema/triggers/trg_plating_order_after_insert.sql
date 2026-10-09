-- TRIGGER (outsourcing_plating_orders): trg_plating_order_after_insert
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_plating_order_after_insert`;

DELIMITER $$
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
END$$
DELIMITER ;
