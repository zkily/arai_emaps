-- TABLE: forming_daily_plan_process_run_calendar_meta
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `forming_daily_plan_process_run_calendar_meta` (
  `period_start` date NOT NULL,
  `period_end` date NOT NULL,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`period_start`,`period_end`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別運行日カレンダー保存済みフラグ';

SET FOREIGN_KEY_CHECKS = 1;
