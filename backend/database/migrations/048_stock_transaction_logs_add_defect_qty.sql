-- stock_transaction_logs に defect_qty 列を追加（任意・他画面用）。
-- 成型APSの「不良」集計は transaction_type='不良' の quantity のみを使用する。
SET NAMES utf8mb4;

delimiter ;;
CREATE PROCEDURE _tmp_add_defect_qty_to_stock_transaction_logs()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_transaction_logs' AND COLUMN_NAME = 'defect_qty') = 0 THEN
    ALTER TABLE stock_transaction_logs
    ADD COLUMN `defect_qty` int NULL DEFAULT NULL COMMENT '任意。成型不良集計は transaction_type=不良 の quantity を使用' AFTER `quantity`;
  END IF;
END;;
delimiter ;
CALL _tmp_add_defect_qty_to_stock_transaction_logs();
DROP PROCEDURE IF EXISTS _tmp_add_defect_qty_to_stock_transaction_logs;
