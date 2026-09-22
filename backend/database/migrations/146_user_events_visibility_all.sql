-- 個人イベント：visibility に全社 (all) を追加（コメント更新）
SET NAMES utf8mb4;

ALTER TABLE `user_events`
  MODIFY COLUMN `visibility` varchar(20) NOT NULL DEFAULT 'department'
  COMMENT 'self=個人 department=部内 all=全社';
