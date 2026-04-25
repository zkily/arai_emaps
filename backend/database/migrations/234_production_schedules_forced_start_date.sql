-- ================================================================
-- production_schedules に forced_start_date を追加（開始日強制指定）
-- Version: 234
-- ================================================================

SET NAMES utf8mb4;

SET @col_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'production_schedules'
    AND COLUMN_NAME = 'forced_start_date'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE `production_schedules` ADD COLUMN `forced_start_date` DATE NULL DEFAULT NULL COMMENT ''排産開始日の強制下限（NULL=未指定）'' AFTER `material_date`',
  'SELECT ''Column forced_start_date already exists'' AS msg'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
