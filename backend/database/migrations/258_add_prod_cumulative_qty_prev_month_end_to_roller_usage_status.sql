-- roller_usage_status: 前月末までの生産累計（自動再計算用）
ALTER TABLE `roller_usage_status`
  ADD COLUMN `prod_cumulative_qty_prev_month_end` int NULL DEFAULT 0 COMMENT '生産累計数（前月末まで・自動）' AFTER `prod_cumulative_qty`;
