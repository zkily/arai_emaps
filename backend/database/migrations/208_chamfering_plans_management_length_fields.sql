-- chamfering_plans / chamfering_management に instruction_plans と同様の切断長・展開長を追加（製品マスタ同期用）
SET NAMES utf8mb4;

ALTER TABLE `chamfering_plans`
  ADD COLUMN `cutting_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長' AFTER `lot_number`,
  ADD COLUMN `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長' AFTER `chamfering_length`;

ALTER TABLE `chamfering_management`
  ADD COLUMN `cutting_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長' AFTER `lot_number`,
  ADD COLUMN `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長' AFTER `chamfering_length`;
