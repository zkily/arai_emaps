-- 個人イベント：繰り返し例外日・リマインド確認履歴
SET NAMES utf8mb4;

ALTER TABLE `user_events`
  ADD COLUMN `recurrence_exdates` text DEFAULT NULL COMMENT '除外発生日 JSON ["YYYY-MM-DD",...]' AFTER `recurrence_until`,
  ADD COLUMN `reminded_dates` text DEFAULT NULL COMMENT '確認済み発生日 JSON ["YYYY-MM-DD",...]' AFTER `last_reminded_occurrence`;
