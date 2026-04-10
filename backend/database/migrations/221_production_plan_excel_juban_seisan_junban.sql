-- production_plan_excel: 追加 順番；生産順番 允许 0～99（两位数以内的有效数字）
-- 依赖：表已存在且原约束名为 production_plan_excel_chk_1（仅限制 1,2 时）
-- 若库中约束名不同，请先 SHOW CREATE TABLE production_plan_excel; 后改 DROP CHECK 名称。

ALTER TABLE `production_plan_excel`
  DROP CHECK `production_plan_excel_chk_1`;

ALTER TABLE `production_plan_excel`
  ADD COLUMN `順番` tinyint UNSIGNED NULL DEFAULT NULL COMMENT '順番' AFTER `生産順番`;

ALTER TABLE `production_plan_excel`
  ADD CONSTRAINT `production_plan_excel_chk_seisan_junban` CHECK (`生産順番` >= 0 AND `生産順番` <= 99);
