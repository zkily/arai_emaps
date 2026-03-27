ALTER TABLE schedule_details
  ADD COLUMN remaining_qty INT NOT NULL DEFAULT 0 COMMENT '差分（planned_qty - actual_qty）';

UPDATE schedule_details
SET remaining_qty = GREATEST(COALESCE(planned_qty, 0) - COALESCE(actual_qty, 0), 0);
