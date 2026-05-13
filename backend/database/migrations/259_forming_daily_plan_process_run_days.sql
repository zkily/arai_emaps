-- 工程別計画試算画面：期間×工程ごとの運行日数
CREATE TABLE IF NOT EXISTS forming_daily_plan_process_run_days (
  id INT AUTO_INCREMENT PRIMARY KEY,
  period_start DATE NOT NULL COMMENT '集計期間開始',
  period_end DATE NOT NULL COMMENT '集計期間終了',
  process_key VARCHAR(32) NOT NULL COMMENT 'cutting|chamfering|molding|plating|welding|inspection',
  run_days INT NOT NULL DEFAULT 0 COMMENT '運行日数',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_period_process (period_start, period_end, process_key),
  KEY idx_period (period_start, period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別計画試算・工程別運行日';
