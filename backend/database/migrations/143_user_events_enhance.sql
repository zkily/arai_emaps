-- 個人イベント：繰り返し・リマインド
SET NAMES utf8mb4;

ALTER TABLE `user_events`
  ADD COLUMN `recurrence_rule` varchar(20) DEFAULT NULL COMMENT 'daily|weekly|monthly|yearly' AFTER `color`,
  ADD COLUMN `recurrence_until` date DEFAULT NULL COMMENT '繰り返し終了日' AFTER `recurrence_rule`,
  ADD COLUMN `remind_offset_minutes` int DEFAULT NULL COMMENT '事前リマインド分数（NULL=無効）' AFTER `recurrence_until`,
  ADD COLUMN `remind_at` datetime DEFAULT NULL COMMENT '次回リマインド発火時刻' AFTER `remind_offset_minutes`,
  ADD COLUMN `reminded_at` datetime DEFAULT NULL COMMENT 'リマインド済み時刻' AFTER `remind_at`,
  ADD COLUMN `last_reminded_occurrence` date DEFAULT NULL COMMENT '繰り返し：最後に確認した発生日' AFTER `reminded_at`;
