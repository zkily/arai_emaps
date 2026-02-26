-- 切断指示に備考列を追加
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '備考' AFTER `updated_at`;
