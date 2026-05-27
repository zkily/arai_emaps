-- メッキ投入ボード：段数レイアウトと枠ごとの日历日・時刻（冪等）
SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_drafts'
    AND COLUMN_NAME = 'max_laps'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE aps_plating_plan_drafts ADD COLUMN max_laps INT NOT NULL DEFAULT 1 COMMENT ''ボード段数（周目数）'' AFTER jigs_per_lap',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_board_cards'
    AND COLUMN_NAME = 'lap_work_date'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE aps_plating_plan_board_cards
     ADD COLUMN lap_work_date DATE NULL COMMENT ''当該周目のカレンダー日（表示期間・週次スケジュール用）'' AFTER work_date,
     ADD COLUMN lap_start_time VARCHAR(5) NULL COMMENT ''当該周目開始時刻（HH:mm）'' AFTER lap_work_date,
     ADD COLUMN lap_end_time VARCHAR(5) NULL COMMENT ''当該周目終了時刻（HH:mm）'' AFTER lap_start_time',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_board_cards'
    AND INDEX_NAME = 'idx_aps_plating_board_draft_lap_date'
);
SET @sql := IF(
  @idx_exists = 0,
  'CREATE INDEX idx_aps_plating_board_draft_lap_date ON aps_plating_plan_board_cards (draft_id, lap_work_date, lap_no, turn_seq)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
