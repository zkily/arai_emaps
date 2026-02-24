-- stock_transaction_logs に defect_qty（不良数）列を追加（外注溶接受入の良品/不良を記録）
SET NAMES utf8mb4;

delimiter ;;
CREATE PROCEDURE _tmp_add_defect_qty_to_stock_transaction_logs()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_transaction_logs' AND COLUMN_NAME = 'defect_qty') = 0 THEN
    ALTER TABLE stock_transaction_logs
    ADD COLUMN `defect_qty` int NULL DEFAULT NULL COMMENT '不良数量（外注溶接受入等）' AFTER `quantity`;
  END IF;
END;;
delimiter ;
CALL _tmp_add_defect_qty_to_stock_transaction_logs();
DROP PROCEDURE IF EXISTS _tmp_add_defect_qty_to_stock_transaction_logs;
