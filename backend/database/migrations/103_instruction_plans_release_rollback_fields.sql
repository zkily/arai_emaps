ALTER TABLE instruction_plans
  ADD COLUMN release_cancelled_at DATETIME NULL DEFAULT NULL COMMENT '上游指示撤回日時',
  ADD COLUMN release_cancel_reason VARCHAR(255) NULL DEFAULT NULL COMMENT '上游指示撤回理由',
  ADD COLUMN release_cancel_by VARCHAR(64) NULL DEFAULT NULL COMMENT '上游指示撤回者';
