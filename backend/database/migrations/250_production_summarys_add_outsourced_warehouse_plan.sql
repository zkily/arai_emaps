-- production_summarys に外注倉庫計画カラムを追加
ALTER TABLE `production_summarys`
  ADD COLUMN `outsourced_warehouse_plan` int DEFAULT 0 COMMENT '外注倉庫計画' AFTER `outsourced_warehouse_trend`;
