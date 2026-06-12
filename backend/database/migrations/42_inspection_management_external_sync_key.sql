-- 検査管理指標 Excel 同期：内容ベースの重複防止キー（再実行可能）
SET NAMES utf8mb4;

DELIMITER //
DROP PROCEDURE IF EXISTS add_inspection_management_external_sync_key//
CREATE PROCEDURE add_inspection_management_external_sync_key()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'inspection_management'
        AND COLUMN_NAME = 'external_sync_key') = 0 THEN
    ALTER TABLE `inspection_management`
      ADD COLUMN `external_sync_key` varchar(64) NULL DEFAULT NULL
        COMMENT '外部Excel同期キー（内容ハッシュ・重複防止）' AFTER `remarks`;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'inspection_management'
        AND INDEX_NAME = 'uk_inspection_external_sync_key') = 0 THEN
    ALTER TABLE `inspection_management`
      ADD UNIQUE INDEX `uk_inspection_external_sync_key` (`external_sync_key`);
  END IF;
END//
DELIMITER ;
CALL add_inspection_management_external_sync_key();
DROP PROCEDURE add_inspection_management_external_sync_key;
