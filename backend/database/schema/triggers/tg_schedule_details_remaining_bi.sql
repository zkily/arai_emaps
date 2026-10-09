-- TRIGGER (schedule_details): tg_schedule_details_remaining_bi
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bi`;

DELIMITER $$
CREATE TRIGGER `tg_schedule_details_remaining_bi` BEFORE INSERT ON `schedule_details` FOR EACH ROW BEGIN
    SET NEW.remaining_qty = COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0) - COALESCE(NEW.defect_qty, 0);
END$$
DELIMITER ;
