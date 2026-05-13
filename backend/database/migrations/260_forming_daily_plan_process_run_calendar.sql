-- 工程別運行日：工程×日历日的勾选（稀疏存储）；meta 区分「从未保存」与「已保存（含全日未勾选）」
DROP TABLE IF EXISTS forming_daily_plan_process_run_days;

CREATE TABLE IF NOT EXISTS forming_daily_plan_process_run_calendar_meta (
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (period_start, period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別運行日カレンダー保存済みフラグ';

CREATE TABLE IF NOT EXISTS forming_daily_plan_process_run_calendar (
  id INT AUTO_INCREMENT PRIMARY KEY,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  process_key VARCHAR(32) NOT NULL COMMENT 'cutting|chamfering|molding|plating|welding|inspection',
  calendar_date DATE NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_period_process_cal (period_start, period_end, process_key, calendar_date),
  KEY idx_period (period_start, period_end),
  KEY idx_process (process_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別運行日（チェックされた日のみ保持）';
