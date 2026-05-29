-- aps_plating_plan_board_cards：テーブル・カラムに日本語コメントを付与（冪等・既存 COMMENT を上書き）
-- ※ plan_date / work_date 列は 23 番マイグレーションで削除
SET NAMES utf8mb4;

ALTER TABLE aps_plating_plan_board_cards
  COMMENT = 'メッキ投入スケジュールボード枠（1治具枠＝1行・周目 lap_no／順 turn_seq）';

ALTER TABLE aps_plating_plan_board_cards
  MODIFY COLUMN id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主キー',
  MODIFY COLUMN draft_id INT NOT NULL COMMENT '親ドラフトID（aps_plating_plan_drafts.id）',
  MODIFY COLUMN plan_date DATE NOT NULL COMMENT '計画日（草稿主表 plan_date の冗長保持・日次検索用）',
  MODIFY COLUMN draft_version_no INT NOT NULL DEFAULT 1 COMMENT '保存時草稿バージョン（主表 version_no のスナップショット）',
  MODIFY COLUMN work_date DATE NULL COMMENT '作業日（NULL 時は plan_date 当日・draft_items と同規則）',
  MODIFY COLUMN lap_work_date DATE NULL COMMENT '当該周目のカレンダー日（表示期間・週次スケジュール用）',
  MODIFY COLUMN lap_start_time VARCHAR(5) NULL COMMENT '当該周目開始時刻（HH:mm）',
  MODIFY COLUMN lap_end_time VARCHAR(5) NULL COMMENT '当該周目終了時刻（HH:mm）',
  MODIFY COLUMN lap_no INT NOT NULL COMMENT '周目番号（ボード段番号・永続 lap_no）',
  MODIFY COLUMN turn_seq INT NOT NULL COMMENT '週目内並び順（列への割当順）',
  MODIFY COLUMN product_cd VARCHAR(64) NOT NULL COMMENT '製品コード',
  MODIFY COLUMN product_name VARCHAR(255) NOT NULL COMMENT '製品名',
  MODIFY COLUMN plating_machine VARCHAR(64) NOT NULL COMMENT 'メッキ治具（設備名）',
  MODIFY COLUMN kake DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '掛け数（生産効率・1枠換算）',
  MODIFY COLUMN qty INT NOT NULL DEFAULT 0 COMMENT '割当数量',
  MODIFY COLUMN slots INT NOT NULL DEFAULT 0 COMMENT '枠数（治具本数換算）',
  MODIFY COLUMN board_mark VARCHAR(16) NOT NULL DEFAULT 'standard' COMMENT 'ボードマーク（standard／manual／rush）',
  MODIFY COLUMN stable_key VARCHAR(128) NULL COMMENT '安定キー（③明細・クライアント枠 id との紐付け）',
  MODIFY COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  MODIFY COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時';
