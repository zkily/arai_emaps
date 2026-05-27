-- メッキ計画：追加レイアウトブロック保存表（draft 単位で各ブロックの計画日／段数／設定を保存）
-- 既存環境にも安全に適用可（CREATE IF NOT EXISTS）
-- 実行例: mysql -u USER -p eams_db < backend/database/migrations/22_aps_plating_plan_draft_layouts.sql

CREATE TABLE IF NOT EXISTS aps_plating_plan_draft_layouts (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主キー',
  draft_id INT NOT NULL COMMENT '親ドラフトID（aps_plating_plan_drafts.id）',
  block_seq INT NOT NULL DEFAULT 0 COMMENT 'ブロック並び順（追加レイアウト追加順・0 起点）',
  plan_date DATE NOT NULL COMMENT 'このブロックの計画日（lap_work_date のベース日付）',
  start_time VARCHAR(5) NOT NULL DEFAULT '08:00' COMMENT 'このブロックの開始時刻（HH:mm）',
  minutes_per_lap INT NOT NULL DEFAULT 100 COMMENT '1 周の所要分（メッキ周期）',
  jigs_per_lap INT NOT NULL DEFAULT 100 COMMENT '1 周の治具本数（ボード全体で揃える）',
  lap_count INT NOT NULL DEFAULT 1 COMMENT 'このブロックの周目数',
  base_lap_no INT NOT NULL DEFAULT 1 COMMENT 'グローバル周目番号の起点（このブロックの最初の周目）',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (id),
  KEY idx_aps_plating_layouts_draft_seq (draft_id, block_seq),
  KEY idx_aps_plating_layouts_plan_date (plan_date),
  KEY idx_aps_plating_layouts_draft_plan (draft_id, plan_date),
  CONSTRAINT fk_aps_plating_layouts_draft
    FOREIGN KEY (draft_id) REFERENCES aps_plating_plan_drafts (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='メッキ計画 追加レイアウトブロック（カード未配置でも基本骨格を永続化）';
