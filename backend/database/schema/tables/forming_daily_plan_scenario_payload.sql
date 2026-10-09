-- TABLE: forming_daily_plan_scenario_payload
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `forming_daily_plan_scenario_payload` (
  `scenario_id` int NOT NULL,
  `payload` json NOT NULL COMMENT 'overrides, run_calendar_snapshot, forecast_options, results_cache',
  PRIMARY KEY (`scenario_id`),
  CONSTRAINT `fk_fdp_scenario_payload` FOREIGN KEY (`scenario_id`) REFERENCES `forming_daily_plan_scenarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成型计划试算方案快照';

SET FOREIGN_KEY_CHECKS = 1;
