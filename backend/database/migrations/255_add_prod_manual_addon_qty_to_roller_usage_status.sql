-- ローラー使用状況：単一手入力補正（自動生産累計に加算）
ALTER TABLE `roller_usage_status`
  ADD COLUMN `prod_manual_addon_qty` int NULL DEFAULT 0 COMMENT '手入力補正（自動累計に加算）' AFTER `prod_cumulative_qty`;
