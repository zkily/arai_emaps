-- 溶接管理指標 Excel 同期：内容ベースの重複防止キー・取得元・時間秒列
SET NAMES utf8mb4;

DELIMITER //
DROP PROCEDURE IF EXISTS add_welding_management_external_sync//
CREATE PROCEDURE add_welding_management_external_sync()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'welding_management'
        AND COLUMN_NAME = 'external_sync_key') = 0 THEN
    ALTER TABLE `welding_management`
      ADD COLUMN `external_sync_key` varchar(64) NULL DEFAULT NULL
        COMMENT '外部Excel同期キー（内容ハッシュ・重複防止）' AFTER `remarks`;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'welding_management'
        AND INDEX_NAME = 'uk_welding_external_sync_key') = 0 THEN
    ALTER TABLE `welding_management`
      ADD UNIQUE INDEX `uk_welding_external_sync_key` (`external_sync_key`);
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'welding_management'
        AND COLUMN_NAME = 'data_source') = 0 THEN
    ALTER TABLE `welding_management`
      ADD COLUMN `data_source` varchar(16) NOT NULL DEFAULT 'mes'
        COMMENT '取得元: mes=溶接実績収集, excel=管理指標Excel同期, csv=一括取込'
        AFTER `external_sync_key`;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'welding_management'
        AND INDEX_NAME = 'idx_welding_data_source') = 0 THEN
    ALTER TABLE `welding_management`
      ADD INDEX `idx_welding_data_source` (`data_source`);
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'welding_management'
        AND COLUMN_NAME = 'mes_shift_sec') = 0 THEN
    ALTER TABLE `welding_management`
      ADD COLUMN `mes_shift_sec` INT NULL DEFAULT NULL COMMENT 'Excelシフト秒' AFTER `mes_paused_accum_sec`,
      ADD COLUMN `mes_break_sec` INT NULL DEFAULT NULL COMMENT 'Excel休憩秒' AFTER `mes_shift_sec`,
      ADD COLUMN `mes_stop_sec` INT NULL DEFAULT NULL COMMENT 'Excel停止等秒' AFTER `mes_break_sec`;
  END IF;
END//
DELIMITER ;
CALL add_welding_management_external_sync();
DROP PROCEDURE add_welding_management_external_sync;
