-- TABLE: aps_plating_plan_drafts
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `aps_plating_plan_drafts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plan_date` date NOT NULL,
  `version_no` int NOT NULL DEFAULT '1',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft',
  `daily_minutes` int NOT NULL DEFAULT '600',
  `jigs_per_lap` int NOT NULL DEFAULT '100',
  `max_laps` int NOT NULL DEFAULT '1' COMMENT 'ボード段数（周目数）',
  `minutes_per_lap` int NOT NULL DEFAULT '100',
  `board_start_time` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ボード第1段開始時刻 HH:mm',
  `total_slots` int NOT NULL DEFAULT '0',
  `used_slots` int NOT NULL DEFAULT '0',
  `remain_slots` int NOT NULL DEFAULT '0',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_aps_plating_plan_drafts_date_ver` (`plan_date`,`version_no`),
  KEY `idx_aps_plating_plan_drafts_date` (`plan_date`),
  KEY `idx_aps_plating_plan_drafts_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
