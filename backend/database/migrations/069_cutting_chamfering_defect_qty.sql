-- cutting_management / chamfering_management に不良数（defect_qty）を追加
-- 不良が発生した場合の録入・管理用。実績確定時は良品数（actual_production_quantity）のみ在庫へ計上。
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `defect_qty` int NULL DEFAULT 0 COMMENT '不良数' AFTER `actual_production_quantity`;

ALTER TABLE `chamfering_management`
  ADD COLUMN `defect_qty` int NULL DEFAULT 0 COMMENT '不良数' AFTER `actual_production_quantity`;
