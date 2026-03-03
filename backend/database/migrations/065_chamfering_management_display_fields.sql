-- 面取指示：表示用カラム追加（面取機、生産順、備考）
SET NAMES utf8mb4;

ALTER TABLE `chamfering_management`
  ADD COLUMN `chamfering_machine` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '面取機（手動指定）' AFTER `production_line`,
  ADD COLUMN `production_sequence` int NULL DEFAULT 0 COMMENT '生産順' AFTER `chamfering_machine`,
  ADD COLUMN `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '備考' AFTER `production_time`;

UPDATE `chamfering_management` SET chamfering_machine = production_line WHERE chamfering_machine IS NULL;
UPDATE `chamfering_management` SET production_sequence = COALESCE(production_order, id) WHERE production_sequence IS NULL OR production_sequence = 0;

ALTER TABLE `chamfering_management`
  ADD INDEX `idx_chamfering_machine` (`chamfering_machine`);
