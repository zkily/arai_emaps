-- stock_transaction_logs に notes 列を追加（存在しない場合のみ）
-- 溶接注文削除時に notes = order_no のレコードも削除するため

SET NAMES utf8mb4;

delimiter ;;
CREATE PROCEDURE _tmp_add_notes_to_stock_transaction_logs()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_transaction_logs' AND COLUMN_NAME = 'notes') = 0 THEN
    ALTER TABLE stock_transaction_logs
    ADD COLUMN `notes` varchar(100) NULL DEFAULT NULL COMMENT '注文番号等（トリガー互換・削除照合用）' AFTER `order_no`;
  END IF;
END;;
delimiter ;
CALL _tmp_add_notes_to_stock_transaction_logs();
DROP PROCEDURE _tmp_add_notes_to_stock_transaction_logs;
