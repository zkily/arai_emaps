-- メッキ計画：表が無い環境向け（CREATE IF NOT EXISTS + 列追加はすべて冪等）
-- 実行前に対象 DB を選択: USE eams_db;
-- 例: mysql -u USER -p eams_db < backend/database/migrations/20_ensure_aps_plating_plan_tables.sql
-- 注意: 19 を既に適用済みでも本脚本は再実行可。19 単体の再実行も可（冪等化済み）。

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'aps_plating_plan_drafts' AND COLUMN_NAME = 'board_start_time'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE aps_plating_plan_drafts ADD COLUMN board_start_time VARCHAR(5) NULL COMMENT ''ボード第1段開始 HH:mm'' AFTER minutes_per_lap',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'aps_plating_plan_drafts' AND COLUMN_NAME = 'max_laps'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE aps_plating_plan_drafts ADD COLUMN max_laps INT NOT NULL DEFAULT 1 COMMENT ''ボード段数'' AFTER jigs_per_lap',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS aps_plating_plan_draft_items (
  id BIGINT NOT NULL AUTO_INCREMENT,
  draft_id INT NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  product_cd VARCHAR(64) NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  plating_machine VARCHAR(64) NOT NULL,
  kake DECIMAL(10, 2) NOT NULL DEFAULT 0,
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
    FOREIGN KEY (draft_id) REFERENCES aps_plating_plan_drafts (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'aps_plating_plan_draft_items' AND COLUMN_NAME = 'work_date'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE aps_plating_plan_draft_items ADD COLUMN work_date DATE NULL AFTER sort_order',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_draft_items'
    AND INDEX_NAME = 'idx_aps_plating_plan_draft_items_work_date'
);
SET @sql := IF(
  @idx_exists = 0,
  'CREATE INDEX idx_aps_plating_plan_draft_items_work_date ON aps_plating_plan_draft_items (work_date)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS aps_plating_plan_board_cards (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主キー',
  draft_id INT NOT NULL COMMENT '親ドラフトID（aps_plating_plan_drafts.id）',
  plan_date DATE NOT NULL COMMENT '計画日（草稿主表 plan_date の冗長保持・日次検索用）',
  draft_version_no INT NOT NULL DEFAULT 1 COMMENT '保存時草稿バージョン（主表 version_no のスナップショット）',
  work_date DATE NULL COMMENT '作業日（NULL 時は plan_date 当日・draft_items と同規則）',
  lap_work_date DATE NULL COMMENT '当該周目のカレンダー日（表示期間・週次スケジュール用）',
  lap_start_time VARCHAR(5) NULL COMMENT '当該周目開始時刻（HH:mm）',
  lap_end_time VARCHAR(5) NULL COMMENT '当該周目終了時刻（HH:mm）',
  lap_no INT NOT NULL COMMENT '周目番号（ボード段番号・永続 lap_no）',
  turn_seq INT NOT NULL COMMENT '週目内並び順（列への割当順）',
  product_cd VARCHAR(64) NOT NULL COMMENT '製品コード',
  product_name VARCHAR(255) NOT NULL COMMENT '製品名',
  plating_machine VARCHAR(64) NOT NULL COMMENT 'メッキ治具（設備名）',
  kake DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '掛け数（生産効率・1枠換算）',
  qty INT NOT NULL DEFAULT 0 COMMENT '割当数量',
  slots INT NOT NULL DEFAULT 0 COMMENT '枠数（治具本数換算）',
  board_mark VARCHAR(16) NOT NULL DEFAULT 'standard' COMMENT 'ボードマーク（standard／manual／rush）',
  stable_key VARCHAR(128) NULL COMMENT '安定キー（③明細・クライアント枠 id との紐付け）',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (id),
  KEY idx_aps_plating_board_draft_lap (draft_id, lap_no, turn_seq),
  KEY idx_aps_plating_board_draft_lap_date (draft_id, lap_work_date, lap_no, turn_seq),
  KEY idx_aps_plating_board_plan_work (plan_date, work_date),
  KEY idx_aps_plating_board_product (product_cd),
  CONSTRAINT fk_aps_plating_board_cards_draft
    FOREIGN KEY (draft_id) REFERENCES aps_plating_plan_drafts (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='メッキ投入スケジュールボード枠（1治具枠＝1行・周目 lap_no／順 turn_seq）';

SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'aps_plating_plan_board_cards' AND COLUMN_NAME = 'lap_work_date'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE aps_plating_plan_board_cards
     ADD COLUMN lap_work_date DATE NULL COMMENT ''当該周目のカレンダー日（表示期間・週次スケジュール用）'' AFTER work_date,
     ADD COLUMN lap_start_time VARCHAR(5) NULL COMMENT ''当該周目開始時刻（HH:mm）'' AFTER lap_work_date,
     ADD COLUMN lap_end_time VARCHAR(5) NULL COMMENT ''当該周目終了時刻（HH:mm）'' AFTER lap_start_time',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'aps_plating_plan_board_cards'
    AND INDEX_NAME = 'idx_aps_plating_board_draft_lap_date'
);
SET @sql := IF(
  @idx_exists = 0,
  'CREATE INDEX idx_aps_plating_board_draft_lap_date ON aps_plating_plan_board_cards (draft_id, lap_work_date, lap_no, turn_seq)',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
