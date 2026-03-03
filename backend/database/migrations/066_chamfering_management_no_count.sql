-- 面取指示：カウント無（no_count）カラム追加
SET NAMES utf8mb4;

ALTER TABLE `chamfering_management`
  ADD COLUMN `no_count` tinyint NULL DEFAULT NULL COMMENT 'カウント無' AFTER `production_completed_check`;
