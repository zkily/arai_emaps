-- APS メッキ計画（第③区域ドラフト）保存テーブル

CREATE TABLE IF NOT EXISTS aps_plating_plan_drafts (
  id INT NOT NULL AUTO_INCREMENT,
  plan_date DATE NOT NULL,
  version_no INT NOT NULL DEFAULT 1,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  daily_minutes INT NOT NULL DEFAULT 600,
  jigs_per_lap INT NOT NULL DEFAULT 100,
  minutes_per_lap INT NOT NULL DEFAULT 100,
  total_slots INT NOT NULL DEFAULT 0,
  used_slots INT NOT NULL DEFAULT 0,
  remain_slots INT NOT NULL DEFAULT 0,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_aps_plating_plan_drafts_date_ver (plan_date, version_no),
  KEY idx_aps_plating_plan_drafts_date (plan_date),
  KEY idx_aps_plating_plan_drafts_status (status)
);

CREATE TABLE IF NOT EXISTS aps_plating_plan_draft_items (
  id BIGINT NOT NULL AUTO_INCREMENT,
  draft_id INT NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  product_cd VARCHAR(64) NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  plating_machine VARCHAR(64) NOT NULL,
  kake DECIMAL(10,2) NOT NULL DEFAULT 0,
  qty INT NOT NULL DEFAULT 0,
  slots INT NOT NULL DEFAULT 0,
  source_type VARCHAR(32) NOT NULL,
  source_row_key VARCHAR(128) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_aps_plating_plan_draft_items_draft_sort (draft_id, sort_order),
  KEY idx_aps_plating_plan_draft_items_product_cd (product_cd),
  CONSTRAINT fk_aps_plating_plan_draft_items_draft
    FOREIGN KEY (draft_id) REFERENCES aps_plating_plan_drafts(id)
    ON DELETE CASCADE
);
