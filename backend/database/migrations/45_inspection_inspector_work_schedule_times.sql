-- 検査員所定工時：勤務開始/終了時刻（指定日・指定時間モード用）
SET NAMES utf8mb4;

DELIMITER //
DROP PROCEDURE IF EXISTS add_inspection_inspector_work_schedule_times//
CREATE PROCEDURE add_inspection_inspector_work_schedule_times()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'inspection_inspector_work_schedule'
        AND COLUMN_NAME = 'work_start_time') = 0 THEN
    ALTER TABLE `inspection_inspector_work_schedule`
      ADD COLUMN `work_start_time` TIME NULL COMMENT '勤務開始（指定日/指定時間）' AFTER `scheduled_hours`,
      ADD COLUMN `work_end_time` TIME NULL COMMENT '勤務終了（指定日/指定時間）' AFTER `work_start_time`;
  END IF;
END//
DELIMITER ;
CALL add_inspection_inspector_work_schedule_times();
DROP PROCEDURE add_inspection_inspector_work_schedule_times;

UPDATE menus SET name = '検査員所定工時管理' WHERE code = 'MASTER_INSPECTION_INSPECTOR_WORK_SCHEDULE';
