-- 溶接注文削除時に stock_transaction_logs を order_no で削除できるようにする
-- 1) 既存ログの order_no を notes から補完（notes 列がある場合）
-- 2) トリガーに order_no を追加し、新規挿入でも order_no を設定する

SET NAMES utf8mb4;

-- 既存データ: notes 列がある場合、source_file=outsourcing_welding_orders の order_no を notes から補完
delimiter ;;
CREATE PROCEDURE _tmp_backfill_welding_order_no()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_transaction_logs' AND COLUMN_NAME = 'notes') > 0 THEN
    UPDATE stock_transaction_logs
    SET order_no = TRIM(notes)
    WHERE source_file = 'outsourcing_welding_orders'
      AND (order_no IS NULL OR order_no = '')
      AND notes IS NOT NULL;
  END IF;
END;;
delimiter ;
CALL _tmp_backfill_welding_order_no();
DROP PROCEDURE _tmp_backfill_welding_order_no();

-- トリガー再作成: INSERT に order_no を追加（notes の代わりに order_no に注文番号を入れる）
-- 注: 042 で notes に NEW.order_no を入れているため、043 では order_no も同じ値で設定する

DROP TRIGGER IF EXISTS `trg_welding_order_after_insert`;
delimiter ;;
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
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `trg_welding_order_after_update`;
delimiter ;;
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
END
;;
delimiter ;
