-- ラベル枚数管理：備考 → 最終発行・印刷履歴
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS migrate_label_qty_last_issue_history;
DELIMITER //
CREATE PROCEDURE migrate_label_qty_last_issue_history()
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'label_quantity_monthly'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'label_quantity_monthly'
        AND COLUMN_NAME = 'last_issue_history'
    ) THEN
      ALTER TABLE `label_quantity_monthly`
        ADD COLUMN `last_issue_history` VARCHAR(255) NULL COMMENT '最終発行・印刷履歴' AFTER `issue_qty`;
    END IF;

    IF EXISTS (
      SELECT 1 FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'label_quantity_monthly'
        AND COLUMN_NAME = 'note'
    ) THEN
      UPDATE `label_quantity_monthly`
      SET `last_issue_history` = COALESCE(`last_issue_history`, `note`)
      WHERE `note` IS NOT NULL AND `note` <> '';
      ALTER TABLE `label_quantity_monthly` DROP COLUMN `note`;
    END IF;
  END IF;
END//
DELIMITER ;

CALL migrate_label_qty_last_issue_history();
DROP PROCEDURE IF EXISTS migrate_label_qty_last_issue_history;
