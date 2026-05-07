-- machines.available_qty（再実行しても 1060 にならない）
SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'machines'
    AND COLUMN_NAME = 'available_qty'
);

SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE machines ADD COLUMN available_qty INT NULL DEFAULT 0 COMMENT ''可用数量'' AFTER efficiency',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
