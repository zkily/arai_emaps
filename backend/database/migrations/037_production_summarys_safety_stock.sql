-- production_summarys に「安全在庫」カラムを追加
ALTER TABLE `production_summarys`
  ADD COLUMN `safety_stock` int NULL DEFAULT 0 COMMENT '安全在庫' AFTER `forecast_quantity`;
