-- TRIGGER (outsourcing_welding_orders): trg_welding_order_after_insert
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_welding_order_after_insert`;

DELIMITER $$
CREATE TRIGGER `trg_welding_order_after_insert` AFTER INSERT ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
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
            CONCAT('外注溶接注文: ', NEW.product_name, ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_welding_orders'
        );
    END IF;
END$$
DELIMITER ;
