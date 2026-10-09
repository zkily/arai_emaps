-- TABLE: process_machine_plan_scenario_payload
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `process_machine_plan_scenario_payload` (
  `scenario_id` int NOT NULL,
  `payload` json NOT NULL COMMENT 'rules, processes_filter, last_simulation',
  PRIMARY KEY (`scenario_id`),
  CONSTRAINT `fk_pmp_scenario_payload` FOREIGN KEY (`scenario_id`) REFERENCES `process_machine_plan_scenarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別設備別計画・調整試算方案ペイロード';

SET FOREIGN_KEY_CHECKS = 1;
