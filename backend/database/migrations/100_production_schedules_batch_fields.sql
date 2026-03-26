-- 100: production_schedules に批次数・ロットサイズスナップショットを追加
ALTER TABLE production_schedules
  ADD COLUMN planned_batch_count INT NOT NULL DEFAULT 0,
  ADD COLUMN lot_size_snapshot   INT NOT NULL DEFAULT 0;
