-- TABLE: forming_daily_plan_process_run_calendar
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `forming_daily_plan_process_run_calendar` (
  `id` int NOT NULL AUTO_INCREMENT,
  `period_start` date NOT NULL,
  `period_end` date NOT NULL,
  `process_key` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'cutting|chamfering|molding|plating|welding|inspection',
  `calendar_date` date NOT NULL,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_period_process_cal` (`period_start`,`period_end`,`process_key`,`calendar_date`),
  KEY `idx_period` (`period_start`,`period_end`),
  KEY `idx_process` (`process_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別運行日（チェックされた日のみ保持）';

SET FOREIGN_KEY_CHECKS = 1;
