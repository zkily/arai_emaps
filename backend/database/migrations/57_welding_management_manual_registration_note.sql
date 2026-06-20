-- 溶接実績収集登録：手動登録備考
SET NAMES utf8mb4;

DELIMITER //
DROP PROCEDURE IF EXISTS add_welding_management_manual_registration_note//
CREATE PROCEDURE add_welding_management_manual_registration_note()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'welding_management'
        AND COLUMN_NAME = 'manual_registration_note') = 0 THEN
    ALTER TABLE `welding_management`
      ADD COLUMN `manual_registration_note` TEXT NULL COMMENT '実績収集登録備考' AFTER `remarks`;
  END IF;
END//
DELIMITER ;
CALL add_welding_management_manual_registration_note();
DROP PROCEDURE add_welding_management_manual_registration_note;
