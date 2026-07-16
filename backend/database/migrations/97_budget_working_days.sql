-- 予算管理：月次稼働日数

CREATE TABLE IF NOT EXISTS budget_working_days (
  id BIGINT NOT NULL AUTO_INCREMENT,
  year SMALLINT NOT NULL COMMENT '年',
  month TINYINT NOT NULL COMMENT '月',
  working_days INT NOT NULL DEFAULT 0 COMMENT '稼働日数',
  remark VARCHAR(255) NULL,
  updated_by VARCHAR(100) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_budget_working_days_ym (year, month),
  KEY idx_budget_working_days_ym (year, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='予算分析用 月次稼働日数';
