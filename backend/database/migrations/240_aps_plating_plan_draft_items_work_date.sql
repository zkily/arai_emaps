ALTER TABLE aps_plating_plan_draft_items
  ADD COLUMN work_date DATE NULL AFTER sort_order;

CREATE INDEX idx_aps_plating_plan_draft_items_work_date
  ON aps_plating_plan_draft_items (work_date);
