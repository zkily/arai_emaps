-- aps_plating_plan_board_cards：plan_date / work_date を廃止し lap_work_date のみに統一（冪等）

UPDATE aps_plating_plan_board_cards
SET lap_work_date = COALESCE(lap_work_date, work_date, plan_date)
WHERE lap_work_date IS NULL;

SET @idx_plan_work := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_board_cards'
    AND INDEX_NAME = 'idx_aps_plating_board_plan_work'
);
SET @sql := IF(
  @idx_plan_work > 0,
  'ALTER TABLE aps_plating_plan_board_cards DROP INDEX idx_aps_plating_board_plan_work',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_work := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_board_cards'
    AND COLUMN_NAME = 'work_date'
);
SET @sql := IF(
  @col_work > 0,
  'ALTER TABLE aps_plating_plan_board_cards DROP COLUMN work_date',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_plan := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_board_cards'
    AND COLUMN_NAME = 'plan_date'
);
SET @sql := IF(
  @col_plan > 0,
  'ALTER TABLE aps_plating_plan_board_cards DROP COLUMN plan_date',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

ALTER TABLE aps_plating_plan_board_cards
  MODIFY COLUMN lap_work_date DATE NOT NULL COMMENT '当該周目のカレンダー日（表示期間・週次スケジュール用）';

-- 23 適用後のコメント（plan_date / work_date 削除済み）
ALTER TABLE aps_plating_plan_board_cards
  MODIFY COLUMN draft_version_no INT NOT NULL DEFAULT 1 COMMENT '保存時草稿バージョン（主表 version_no のスナップショット）';
