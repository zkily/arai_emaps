-- 成型工程计划试算：草稿方案主表 + JSON 快照
CREATE TABLE IF NOT EXISTS forming_daily_plan_scenarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL COMMENT '方案名',
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  base_month CHAR(7) NOT NULL COMMENT '基准月 YYYY-MM',
  status ENUM('draft', 'applied', 'archived') NOT NULL DEFAULT 'draft',
  created_by VARCHAR(64) NULL,
  applied_at DATETIME NULL,
  applied_by VARCHAR(64) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_period (period_start, period_end),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成型计划试算方案';

CREATE TABLE IF NOT EXISTS forming_daily_plan_scenario_payload (
  scenario_id INT NOT NULL PRIMARY KEY,
  payload JSON NOT NULL COMMENT 'overrides, run_calendar_snapshot, forecast_options, results_cache',
  CONSTRAINT fk_fdp_scenario_payload FOREIGN KEY (scenario_id)
    REFERENCES forming_daily_plan_scenarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成型计划试算方案快照';
