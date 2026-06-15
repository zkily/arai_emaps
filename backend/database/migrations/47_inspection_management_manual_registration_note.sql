-- inspection_management 実績収集登録（手動登録）用備考
SET NAMES utf8mb4;

DELIMITER //
DROP PROCEDURE IF EXISTS add_inspection_management_manual_registration_note//
CREATE PROCEDURE add_inspection_management_manual_registration_note()
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'inspection_management' AND column_name = 'manual_registration_note'
  ) THEN
    ALTER TABLE `inspection_management`
      ADD COLUMN `manual_registration_note` TEXT NULL COMMENT '実績収集登録備考' AFTER `remarks`;
  END IF;
END//
DELIMITER ;
CALL add_inspection_management_manual_registration_note();
DROP PROCEDURE add_inspection_management_manual_registration_note;
