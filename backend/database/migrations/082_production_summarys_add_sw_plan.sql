-- production_summarys に sw_plan カラムを追加（計画データ更新で molding_actual_plan を同期するため）
ALTER TABLE `production_summarys`
  ADD COLUMN `sw_plan` int DEFAULT 0 COMMENT 'sw計画（molding_actual_planと同期）' AFTER `sw_machine`;
