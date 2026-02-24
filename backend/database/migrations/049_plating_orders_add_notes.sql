-- 049: outsourcing_plating_orders に notes 列を追加
-- 理由: 本テーブルに対するトリガーが stock_transaction_logs に書き込む際、
--       order_no と source_file を使用する。notes は trigger 互換用に追加（アプリは remarks のみ使用）。
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS _tmp_plating_orders_add_notes;
delimiter ;;
CREATE PROCEDURE _tmp_plating_orders_add_notes()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'outsourcing_plating_orders' AND COLUMN_NAME = 'notes') = 0 THEN
    ALTER TABLE outsourcing_plating_orders
      ADD COLUMN `notes` TEXT NULL COMMENT '備考(trigger互換)' AFTER `remarks`;
  END IF;
END;;
delimiter ;
CALL _tmp_plating_orders_add_notes();
DROP PROCEDURE IF EXISTS _tmp_plating_orders_add_notes;
