-- CP-SAT ジョブをロット単位で識別する列
ALTER TABLE cpsat_jobs
  ADD COLUMN lot_size INT NOT NULL DEFAULT 0 COMMENT '製品ロットサイズ（本）。1以下は未分割' AFTER q_start;

ALTER TABLE cpsat_jobs
  ADD COLUMN lot_index INT NOT NULL DEFAULT 1 COMMENT '当該日・製品内のロット番号（1始まり）' AFTER lot_size;

ALTER TABLE cpsat_jobs
  ADD COLUMN lot_count INT NOT NULL DEFAULT 1 COMMENT '当該日・製品のロット数' AFTER lot_index;
