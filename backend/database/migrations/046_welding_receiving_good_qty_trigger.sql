-- 外注溶接受入：good_qty 変更時に注文入庫数・溶接品在庫・入出庫履歴を更新（検証済み修正版）
-- 状態「受入完」: 受入数合计 >= 注文数 で判定（良品数ではなく）。入庫数(received_qty)は良品累計のまま。
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_welding_receiving_after_update_good_qty`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_update_good_qty` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE good_qty_diff INT DEFAULT 0;
    DECLARE total_received INT DEFAULT 0;   -- 该订单受入数合计（各受入记录的 receiving_qty 之和）
    DECLARE order_qty_val INT DEFAULT 0;    -- 注文数

    SET good_qty_diff = COALESCE(NEW.good_qty, 0) - COALESCE(OLD.good_qty, 0);

    IF good_qty_diff != 0 THEN
        -- 受入完判定用：该订单的受入数合计 与 注文数
        SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
        FROM outsourcing_welding_receivings WHERE order_id = NEW.order_id;
        SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = NEW.order_id LIMIT 1;

        -- 注文：入庫数=良品累計、状態=受入数合计>=注文数なら completed、否则良品>0 なら partial
        UPDATE outsourcing_welding_orders
        SET received_qty = GREATEST(0, received_qty + good_qty_diff),
            status = CASE
                WHEN total_received >= order_qty_val THEN 'completed'
                WHEN received_qty + good_qty_diff > 0 THEN 'partial'
                ELSE 'ordered'
            END
        WHERE id = NEW.order_id;

        -- 在庫テーブル：増加時は先 UPDATE、該当行がなければ INSERT（NULL welding_type でも一意扱い）
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
            -- 減少時は 1 行のみ更新（複数行マッチ時の二重減算を防止）
            UPDATE outsourcing_welding_stock
            SET received_qty = GREATEST(0, received_qty + good_qty_diff)
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type <=> NEW.welding_type)
            ORDER BY id
            LIMIT 1;
        END IF;

        -- 入庫履歴（good_qty_diff != 0 は既に外側で保証されているため IF 不要）
        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date,
            'receive',
            'welding',
            NEW.product_cd,
            NEW.product_name,
            NEW.supplier_cd,
            NEW.receiving_no,
            good_qty_diff,
            NEW.inspector
        );
    END IF;
END
;;
delimiter ;
