-- 生産検討会 工程能力に稼働日を追加
SET NAMES utf8mb4;

ALTER TABLE `production_review_capacity`
  ADD COLUMN `working_days` int NOT NULL DEFAULT 0 COMMENT '稼働日数（0=対象月カレンダー）' AFTER `shift_label`;
