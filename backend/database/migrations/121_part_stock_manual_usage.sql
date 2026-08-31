-- part_stock に手動使用数を追加。
-- 溶接実績由来の planned_usage（使用数）とは独立し、在庫計算で上書きされない。
-- 現在在庫・在庫推移は planned_usage + manual_usage を使用数として減算する。

SET NAMES utf8mb4;

DELIMITER //
DROP PROCEDURE IF EXISTS add_part_stock_manual_usage//
CREATE PROCEDURE add_part_stock_manual_usage()
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'part_stock' AND column_name = 'manual_usage'
  ) THEN
    ALTER TABLE `part_stock`
      ADD COLUMN `manual_usage` int NOT NULL DEFAULT 0 COMMENT '手動使用数' AFTER `planned_usage`;
  END IF;
END//
DELIMITER ;
CALL add_part_stock_manual_usage();
DROP PROCEDURE add_part_stock_manual_usage;
