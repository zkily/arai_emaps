-- sales_order: 納入先名（一覧・詳細表示用）
SET NAMES utf8mb4;

SET @col := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order' AND COLUMN_NAME = 'destination_name'
);
SET @ddl := IF(
  @col = 0,
  'ALTER TABLE sales_order ADD COLUMN destination_name VARCHAR(200) NULL COMMENT ''納入先名'' AFTER destination_cd',
  'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 既存行: customer_name を納入先名表示のフォールバックとしてコピー（destination_name が空の場合）
UPDATE sales_order
SET destination_name = customer_name
WHERE destination_name IS NULL AND customer_name IS NOT NULL AND customer_name != '';
