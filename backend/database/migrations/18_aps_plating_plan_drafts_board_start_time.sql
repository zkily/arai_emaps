-- メッキ投入ボード：標準レイアウトの第1段開始時刻（HH:mm）（冪等）
SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_drafts'
    AND COLUMN_NAME = 'board_start_time'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE aps_plating_plan_drafts ADD COLUMN board_start_time VARCHAR(5) NULL DEFAULT NULL COMMENT ''ボード第1段開始時刻 HH:mm'' AFTER minutes_per_lap',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
