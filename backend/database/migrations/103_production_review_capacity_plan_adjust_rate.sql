-- 生産検討会 工程能力に計画調整率(%)を追加
-- 表示計画(千本) = 元計画(千本) × 計画調整率(%) ÷ 100
SET NAMES utf8mb4;

ALTER TABLE `production_review_capacity`
  ADD COLUMN `plan_adjust_rate_pct` decimal(8, 2) NOT NULL DEFAULT 100.00 COMMENT '計画調整率(%) 計画(千本)×調整率' AFTER `utilization_rate_pct`;
