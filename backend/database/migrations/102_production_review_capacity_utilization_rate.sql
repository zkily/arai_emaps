-- 生産検討会 工程能力に稼働率(%)を追加（定時H計算の96%固定を置換）
SET NAMES utf8mb4;

ALTER TABLE `production_review_capacity`
  ADD COLUMN `utilization_rate_pct` decimal(5, 2) NOT NULL DEFAULT 96.00 COMMENT '稼働率(%) 定時H計算用' AFTER `working_days`;
