-- 個人イベント：可視性（self=私密 / department=部門内）
SET NAMES utf8mb4;

ALTER TABLE `user_events`
  ADD COLUMN `visibility` varchar(20) NOT NULL DEFAULT 'department'
  COMMENT 'self=私密 department=部門内'
  AFTER `color`;
