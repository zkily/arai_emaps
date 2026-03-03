-- 面取指示テーブルにロット数・ロットNo・SW工程を追加（面取バッチ一覧へ拖回時にデータ保持）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `chamfering_management`
  ADD COLUMN `production_lot_size` int NULL DEFAULT NULL COMMENT 'ロット数' AFTER `actual_production_quantity`,
  ADD COLUMN `lot_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo' AFTER `production_lot_size`,
  ADD COLUMN `has_sw_process` tinyint NULL DEFAULT NULL COMMENT 'SW工程' AFTER `management_code`;

SET FOREIGN_KEY_CHECKS = 1;
