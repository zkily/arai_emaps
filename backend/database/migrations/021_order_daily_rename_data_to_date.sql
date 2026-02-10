-- order_daily テーブルの data カラムを date にリネーム
-- Version: 021

SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `order_daily`
  CHANGE COLUMN `data` `date` date NOT NULL COMMENT '年月日';

-- インデックス名が idx_order_daily_data の場合はリネーム（017 で定義されている場合）
-- MySQL では CHANGE COLUMN でカラム名変更してもインデックスは自動で付くので、必要なら別途 DROP INDEX + CREATE INDEX

SET FOREIGN_KEY_CHECKS = 1;
