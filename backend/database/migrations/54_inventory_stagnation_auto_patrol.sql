-- 在庫停滞アラート：自動巡検スケジュール（notification_settings）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `notification_settings`
  ADD COLUMN `auto_schedule_enabled` tinyint(1) NOT NULL DEFAULT 0 COMMENT '自動スケジュール有効' AFTER `is_active`,
  ADD COLUMN `auto_schedule_time` time NULL DEFAULT NULL COMMENT '自動実行時刻（JST）' AFTER `auto_schedule_enabled`,
  ADD COLUMN `schedule_config` json NULL COMMENT '自動実行パラメータ JSON' AFTER `auto_schedule_time`;

UPDATE `notification_settings`
SET
  `auto_schedule_enabled` = 1,
  `auto_schedule_time` = '08:00:00',
  `schedule_config` = JSON_OBJECT('min_quantity', 50, 'stable_calendar_days', 7)
WHERE `event_code` = 'INVENTORY_STAGNATION';

SET FOREIGN_KEY_CHECKS = 1;
