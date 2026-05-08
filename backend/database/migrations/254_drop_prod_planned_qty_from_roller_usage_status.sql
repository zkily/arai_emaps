-- roller_usage_status から未使用列 prod_planned_qty（生産予定数）を削除
ALTER TABLE `roller_usage_status`
  DROP COLUMN `prod_planned_qty`;
