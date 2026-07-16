-- 予算管理：工程別稼働日数（未設定時は共通の月次稼働日を使用）

CREATE TABLE IF NOT EXISTS budget_process_working_days (
  id BIGINT NOT NULL AUTO_INCREMENT,
  year SMALLINT NOT NULL COMMENT '年',
  month TINYINT NOT NULL COMMENT '月',
  process_cd VARCHAR(50) NOT NULL COMMENT '工程CD',
  process_name VARCHAR(100) NULL COMMENT '工程名',
  working_days INT NOT NULL DEFAULT 0 COMMENT '工程別稼働日数',
  remark VARCHAR(255) NULL,
  updated_by VARCHAR(100) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_budget_proc_wd_ym_pc (year, month, process_cd),
  KEY idx_budget_proc_wd_ym (year, month),
  KEY idx_budget_proc_wd_pc (process_cd)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='予算分析用 工程別月次稼働日数';
