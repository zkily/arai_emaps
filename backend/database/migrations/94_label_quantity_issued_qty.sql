-- ラベル枚数管理：発行済（実印刷枚数）
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS migrate_label_qty_issued_qty;
DELIMITER //
CREATE PROCEDURE migrate_label_qty_issued_qty()
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'label_quantity_monthly'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'label_quantity_monthly'
        AND COLUMN_NAME = 'issued_qty'
    ) THEN
      ALTER TABLE `label_quantity_monthly`
        ADD COLUMN `issued_qty` INT NOT NULL DEFAULT 0
          COMMENT '発行済枚数（印刷実績の累計）'
          AFTER `issue_qty`;
    END IF;
  END IF;
END//
DELIMITER ;

CALL migrate_label_qty_issued_qty();
DROP PROCEDURE IF EXISTS migrate_label_qty_issued_qty;
