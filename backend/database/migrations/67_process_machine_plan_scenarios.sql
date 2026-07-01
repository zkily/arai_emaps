-- 工程別設備別計画：調整試算方案（シミュレーション保存用、production_summarys へは書き込まない）
CREATE TABLE IF NOT EXISTS process_machine_plan_scenarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL COMMENT '方案名',
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  status ENUM('draft', 'archived') NOT NULL DEFAULT 'draft',
  created_by VARCHAR(64) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_pmp_period (period_start, period_end),
  KEY idx_pmp_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別設備別計画・調整試算方案';

CREATE TABLE IF NOT EXISTS process_machine_plan_scenario_payload (
  scenario_id INT NOT NULL PRIMARY KEY,
  payload JSON NOT NULL COMMENT 'rules, processes_filter, last_simulation',
  CONSTRAINT fk_pmp_scenario_payload FOREIGN KEY (scenario_id)
    REFERENCES process_machine_plan_scenarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別設備別計画・調整試算方案ペイロード';
