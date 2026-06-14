-- inspection_management CSV 時間列（シフト / 休憩 / 停止）を秒で保持
SET NAMES utf8mb4;

DELIMITER //
DROP PROCEDURE IF EXISTS add_inspection_management_csv_time_sec//
CREATE PROCEDURE add_inspection_management_csv_time_sec()
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'inspection_management' AND column_name = 'mes_shift_sec'
  ) THEN
    ALTER TABLE `inspection_management`
      ADD COLUMN `mes_shift_sec` INT NULL DEFAULT NULL COMMENT 'CSVシフト秒' AFTER `mes_paused_accum_sec`,
      ADD COLUMN `mes_break_sec` INT NULL DEFAULT NULL COMMENT 'CSV休憩秒' AFTER `mes_shift_sec`,
      ADD COLUMN `mes_stop_sec` INT NULL DEFAULT NULL COMMENT 'CSV停止(段替等)秒' AFTER `mes_break_sec`;
  END IF;
END//
DELIMITER ;
CALL add_inspection_management_csv_time_sec();
DROP PROCEDURE add_inspection_management_csv_time_sec;
