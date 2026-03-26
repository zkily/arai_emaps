-- 102: instruction_plans に APS バッチ参照ID を追加
SET NAMES utf8mb4;

ALTER TABLE `instruction_plans`
  ADD COLUMN `aps_batch_plan_id` int NULL DEFAULT NULL COMMENT 'APS 批次計画（aps_batch_plans.id）参照';

