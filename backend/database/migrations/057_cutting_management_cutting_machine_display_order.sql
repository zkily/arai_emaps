-- 切断指示：切断機（手動指定）と生産順（按切断機自動排序・可拖拽変更）
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `cutting_machine` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '切断機（手動指定）' AFTER `production_line`,
  ADD COLUMN `production_sequence` int NULL DEFAULT 0 COMMENT '生産順（同一切断機内の自動並び順、拖拽可変更）' AFTER `cutting_machine`;

UPDATE `cutting_management` SET cutting_machine = production_line WHERE cutting_machine IS NULL;
UPDATE `cutting_management` SET production_sequence = id WHERE production_sequence IS NULL OR production_sequence = 0;

ALTER TABLE `cutting_management`
  ADD INDEX `idx_cutting_machine` (`cutting_machine`),
  ADD INDEX `idx_production_sequence` (`production_sequence`);
