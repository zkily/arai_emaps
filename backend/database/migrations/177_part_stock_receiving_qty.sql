-- 部品在庫: 受入数を追加。在庫計算は注文数ではなく受入数を用いる。
-- 既存データの在庫水準を維持するため、列追加直後のみ受入数へ注文数を初期コピーする。
SET NAMES utf8mb4;

SET @col_exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'part_stock'
    AND COLUMN_NAME = 'receiving_qty'
);

SET @sql = IF(
  @col_exists = 0,
  'ALTER TABLE `part_stock` ADD COLUMN `receiving_qty` int NOT NULL DEFAULT 0 COMMENT ''受入数'' AFTER `order_quantity`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 列が無かった場合のみバックフィル（再実行で意図的な 0 を上書きしない）
SET @sql = IF(
  @col_exists = 0,
  'UPDATE `part_stock` SET `receiving_qty` = COALESCE(`order_quantity`, 0) WHERE COALESCE(`order_quantity`, 0) <> 0',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
