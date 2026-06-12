-- inspection_management 実績の取得元（mes / excel / csv）
SET NAMES utf8mb4;

DELIMITER //
DROP PROCEDURE IF EXISTS add_inspection_management_data_source//
CREATE PROCEDURE add_inspection_management_data_source()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'inspection_management'
        AND COLUMN_NAME = 'data_source') = 0 THEN
    ALTER TABLE `inspection_management`
      ADD COLUMN `data_source` varchar(16) NOT NULL DEFAULT 'mes'
        COMMENT '取得元: mes=検査実績収集, excel=管理指標Excel同期, csv=一括取込'
        AFTER `external_sync_key`;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'inspection_management'
        AND INDEX_NAME = 'idx_inspection_data_source') = 0 THEN
    ALTER TABLE `inspection_management`
      ADD INDEX `idx_inspection_data_source` (`data_source`);
  END IF;
  UPDATE `inspection_management`
  SET `data_source` = 'excel'
  WHERE (`external_sync_key` IS NOT NULL AND `external_sync_key` <> '')
     OR (`remarks` LIKE 'EXCEL_SYNC:%');
  UPDATE `inspection_management`
  SET `data_source` = 'csv'
  WHERE `remarks` LIKE 'CSV_IMPORT:%';
  UPDATE `inspection_management`
  SET `data_source` = 'mes'
  WHERE `data_source` IS NULL OR `data_source` = '';
END//
DELIMITER ;
CALL add_inspection_management_data_source();
DROP PROCEDURE add_inspection_management_data_source;
