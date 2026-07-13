-- ラベル枚数管理：月初手動ロック（再計算時に上書きしない）
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS migrate_label_qty_opening_locked;
DELIMITER //
CREATE PROCEDURE migrate_label_qty_opening_locked()
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'label_quantity_monthly'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'label_quantity_monthly'
        AND COLUMN_NAME = 'opening_locked'
    ) THEN
      ALTER TABLE `label_quantity_monthly`
        ADD COLUMN `opening_locked` TINYINT(1) NOT NULL DEFAULT 0
          COMMENT '月初在庫手動ロック（1=再計算で上書きしない）'
          AFTER `opening_stock`;
    END IF;
  END IF;
END//
DELIMITER ;

CALL migrate_label_qty_opening_locked();
DROP PROCEDURE IF EXISTS migrate_label_qty_opening_locked;
