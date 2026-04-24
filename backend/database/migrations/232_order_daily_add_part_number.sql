-- ================================================================
-- order_daily テーブルに part_number カラムを追加（EDI かんばん取込で使用）
-- Version: 232
-- ================================================================

SET NAMES utf8mb4;

-- 1) part_number カラム追加（既に存在する場合はスキップ）
SET @col_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'order_daily'
    AND COLUMN_NAME = 'part_number'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE `order_daily` ADD COLUMN `part_number` varchar(50) NULL DEFAULT NULL COMMENT ''EDI かんばん品番（hinban）'' AFTER `product_cd`',
  'SELECT ''Column part_number already exists'' AS msg'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2) part_number にインデックスを付与（EDI 取込時の検索高速化）
SET @idx_exists := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'order_daily'
    AND INDEX_NAME = 'idx_order_daily_part_number'
);

SET @idx_ddl := IF(
  @idx_exists = 0,
  'CREATE INDEX `idx_order_daily_part_number` ON `order_daily` (`part_number`)',
  'SELECT ''Index idx_order_daily_part_number already exists'' AS msg'
);

PREPARE stmt2 FROM @idx_ddl;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;
