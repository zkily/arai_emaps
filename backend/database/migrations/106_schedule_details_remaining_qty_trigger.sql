-- schedule_details.remaining_qty を planned_qty / actual_qty から自動算出

DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bi`;
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bu`;

DELIMITER $$

CREATE TRIGGER `tg_schedule_details_remaining_bi`
BEFORE INSERT ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = GREATEST(COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0), 0);
END$$

CREATE TRIGGER `tg_schedule_details_remaining_bu`
BEFORE UPDATE ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = GREATEST(COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0), 0);
END$$

DELIMITER ;

-- 既存データ補正
UPDATE schedule_details
SET remaining_qty = GREATEST(COALESCE(planned_qty, 0) - COALESCE(actual_qty, 0), 0);
