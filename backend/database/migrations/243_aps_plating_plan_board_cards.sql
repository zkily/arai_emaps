-- APS メッキ計画 第④看板枠（周回内順序）子表：与草稿主表 plan_date / version 一并落库便于查询与追溯

CREATE TABLE IF NOT EXISTS aps_plating_plan_board_cards (
  id BIGINT NOT NULL AUTO_INCREMENT,
  draft_id INT NOT NULL,
  plan_date DATE NOT NULL COMMENT '计划日（与 aps_plating_plan_drafts.plan_date 冗余，便于按日查询）',
  draft_version_no INT NOT NULL DEFAULT 1 COMMENT '写入时草稿版本号（与主表 version_no 快照一致）',
  work_date DATE NULL COMMENT '作業日；NULL 表示沿用 plan_date 当日（与 draft_items 规则一致）',
  lap_no INT NOT NULL,
  turn_seq INT NOT NULL,
  product_cd VARCHAR(64) NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  plating_machine VARCHAR(64) NOT NULL,
  kake DECIMAL(10, 2) NOT NULL DEFAULT 0,
  qty INT NOT NULL DEFAULT 0,
  slots INT NOT NULL DEFAULT 0,
  board_mark VARCHAR(16) NOT NULL DEFAULT 'standard',
  stable_key VARCHAR(128) NULL COMMENT '可选：与③行或客户端枠 id 关联',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_aps_plating_board_draft_lap (draft_id, lap_no, turn_seq),
  KEY idx_aps_plating_board_plan_work (plan_date, work_date),
  KEY idx_aps_plating_board_product (product_cd),
  CONSTRAINT fk_aps_plating_board_cards_draft
    FOREIGN KEY (draft_id) REFERENCES aps_plating_plan_drafts (id)
    ON DELETE CASCADE
);
