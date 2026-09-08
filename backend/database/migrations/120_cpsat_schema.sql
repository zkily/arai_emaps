-- CP-SAT 排程：主データ補完 + 求解スナップショット／結果表
-- 数学モデル対応:
--   i = 注文(Job), j = 工程(Operation), k = 設備(Machine)
--   X_{i,j,k} / S_{i,j} / E_{i,j} / P_{i,j,k} / T_wait / Y_j / Q_target / D_i
-- 実行例: mysql -u USER -p eams_db < backend/database/migrations/120_cpsat_schema.sql
SET NAMES utf8mb4;

-- ========== 1. 主データ補完 ==========

-- 工程ルートテンプレート: 後工程開始までの最小待ち秒 T_wait
SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'process_route_steps'
    AND COLUMN_NAME = 'wait_sec_after'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE process_route_steps ADD COLUMN wait_sec_after INT NOT NULL DEFAULT 0 COMMENT ''後工程開始までの最小待ち秒（T_wait）'' AFTER cycle_sec',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 製品別ルート: 歩留 Y_j（NULL は工程ルート / 工程マスタへフォールバック）
SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'product_route_steps'
    AND COLUMN_NAME = 'yield_percent'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE product_route_steps ADD COLUMN yield_percent DECIMAL(5,2) NULL DEFAULT NULL COMMENT ''歩留(%)。NULL時は工程ルート/工程マスタ'' AFTER process_cd',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'product_route_steps'
    AND COLUMN_NAME = 'wait_sec_after'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE product_route_steps ADD COLUMN wait_sec_after INT NULL DEFAULT NULL COMMENT ''後工程開始までの最小待ち秒。NULL時は工程ルート既定'' AFTER yield_percent',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 設備: CP-SAT の候補集合 k に含めるか
SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'machines'
    AND COLUMN_NAME = 'use_in_cpsat'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE machines ADD COLUMN use_in_cpsat TINYINT(1) NOT NULL DEFAULT 1 COMMENT ''CP-SAT自動排程に参加するか'' AFTER status',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- P_{i,j,k} 原単位: 1本あたり秒。DECIMAL(4,2) は 99.99 秒上限のため拡張
ALTER TABLE product_route_step_machines
  MODIFY COLUMN process_time_sec DECIMAL(10, 2) NOT NULL DEFAULT 0.00
  COMMENT '1本あたり加工時間(秒)。バッチ加工時間 P は数量×本秒で算出';

-- 既存製品ステップへテンプレート歩留をバックフィル（未設定のみ）
UPDATE product_route_steps prs
LEFT JOIN process_route_steps t
  ON t.route_cd = prs.route_cd AND t.process_cd = prs.process_cd
LEFT JOIN processes proc
  ON proc.process_cd = prs.process_cd
SET prs.yield_percent = COALESCE(t.yield_percent, proc.default_yield * 100, 100)
WHERE prs.yield_percent IS NULL;

UPDATE product_route_steps
SET wait_sec_after = 0
WHERE wait_sec_after IS NULL;

-- ========== 2. CP-SAT 求解結果（ジョブ展開のスナップショット。既存 APS 工単とは分離） ==========

CREATE TABLE IF NOT EXISTS cpsat_runs (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '求解実行ID',
  run_code VARCHAR(40) NULL COMMENT '表示用コード（例: CPSAT-20260904-001）',
  name VARCHAR(100) NULL COMMENT '実行名',
  horizon_start DATETIME NOT NULL COMMENT '計画期間開始（S/E の原点）',
  horizon_end DATETIME NOT NULL COMMENT '計画期間終了',
  time_unit_sec INT NOT NULL DEFAULT 60 COMMENT 'CP-SAT 整数時間の1単位（秒）',
  objective_type VARCHAR(20) NOT NULL DEFAULT 'tardiness' COMMENT 'makespan / tardiness / weighted',
  makespan_weight DECIMAL(8, 4) NOT NULL DEFAULT 0.0000 COMMENT '加重目的の C_max 係数',
  tardiness_weight DECIMAL(8, 4) NOT NULL DEFAULT 1.0000 COMMENT '加重目的の ΣT_i 係数',
  max_solve_seconds INT NOT NULL DEFAULT 60 COMMENT 'ソルバ上限秒',
  status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/queued/running/optimal/feasible/infeasible/error/cancelled',
  solver_status VARCHAR(40) NULL COMMENT 'OR-Tools 生ステータス',
  wall_time_sec DECIMAL(10, 3) NULL COMMENT '実求解時間（秒）',
  makespan_sec BIGINT NULL COMMENT 'C_max（秒、horizon_start 起点）',
  total_tardiness_sec BIGINT NULL COMMENT 'Σ T_i（秒）',
  objective_value DECIMAL(18, 4) NULL COMMENT '目的関数値',
  job_count INT NOT NULL DEFAULT 0 COMMENT '展開した注文数 i',
  operation_count INT NOT NULL DEFAULT 0 COMMENT '展開した工程数 (i,j)',
  error_message TEXT NULL COMMENT '失敗・実行不能の理由',
  created_by VARCHAR(50) NULL COMMENT '実行者',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cpsat_runs_code (run_code),
  KEY idx_cpsat_runs_status (status),
  KEY idx_cpsat_runs_horizon (horizon_start, horizon_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CP-SAT 求解実行ヘッダ';

CREATE TABLE IF NOT EXISTS cpsat_jobs (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ジョブ行ID',
  run_id BIGINT NOT NULL COMMENT 'cpsat_runs.id',
  job_index INT NOT NULL COMMENT '注文インデックス i',
  source_type VARCHAR(32) NOT NULL COMMENT 'order_daily / production_schedule / manual',
  source_id INT NULL COMMENT '元レコードID',
  order_no VARCHAR(50) NULL COMMENT '表示用受注番号',
  product_cd VARCHAR(50) NOT NULL COMMENT '製品CD',
  product_name VARCHAR(100) NULL COMMENT '製品名',
  q_target INT NOT NULL COMMENT '最終入库量 Q_target',
  q_start INT NOT NULL COMMENT '切断投入量 Q_start = Q_target / Π Y_j',
  due_at DATETIME NULL COMMENT '約束交期 D_i',
  due_sec INT NULL COMMENT 'D_i（horizon 起点秒）',
  last_op_end_sec INT NULL COMMENT '最終工程終了 E_{i,last}',
  tardiness_sec INT NULL COMMENT '遅延 T_i = max(0, E_last - D_i)',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cpsat_jobs_run_index (run_id, job_index),
  KEY idx_cpsat_jobs_product (run_id, product_cd),
  KEY idx_cpsat_jobs_source (source_type, source_id),
  CONSTRAINT fk_cpsat_jobs_run
    FOREIGN KEY (run_id) REFERENCES cpsat_runs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CP-SAT 注文ジョブ i（実行時スナップショット）';

CREATE TABLE IF NOT EXISTS cpsat_operations (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '工程行ID',
  run_id BIGINT NOT NULL COMMENT 'cpsat_runs.id',
  job_id BIGINT NOT NULL COMMENT 'cpsat_jobs.id',
  op_index INT NOT NULL COMMENT '工程インデックス j',
  step_no INT NOT NULL COMMENT '製品ルート step_no',
  process_cd VARCHAR(20) NOT NULL COMMENT '工程CD',
  process_name VARCHAR(60) NULL COMMENT '工程名',
  yield_percent DECIMAL(5, 2) NOT NULL DEFAULT 100.00 COMMENT 'スナップショット歩留 Y_j（%）',
  wait_sec_after INT NOT NULL DEFAULT 0 COMMENT '後工程への T_wait（秒）',
  q_input INT NOT NULL DEFAULT 0 COMMENT '当該工程投入量 Q_j',
  q_output INT NOT NULL DEFAULT 0 COMMENT '歩留後出来高',
  start_sec INT NULL COMMENT '開始 S_{i,j}（horizon 起点秒）',
  end_sec INT NULL COMMENT '終了 E_{i,j}',
  start_at DATETIME NULL COMMENT '開始日時',
  end_at DATETIME NULL COMMENT '終了日時',
  assigned_machine_cd VARCHAR(50) NULL COMMENT '割当設備 k（X=1 の機）',
  assigned_machine_name VARCHAR(100) NULL COMMENT '割当設備名',
  processing_sec INT NULL COMMENT '選択機のバッチ加工時間 P',
  setup_sec INT NULL COMMENT '段取秒',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cpsat_ops_job_index (job_id, op_index),
  KEY idx_cpsat_ops_run (run_id, process_cd),
  KEY idx_cpsat_ops_machine (run_id, assigned_machine_cd, start_sec),
  CONSTRAINT fk_cpsat_ops_run
    FOREIGN KEY (run_id) REFERENCES cpsat_runs (id) ON DELETE CASCADE,
  CONSTRAINT fk_cpsat_ops_job
    FOREIGN KEY (job_id) REFERENCES cpsat_jobs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CP-SAT 工程 j（S/E と割当結果）';

CREATE TABLE IF NOT EXISTS cpsat_candidates (
  id BIGINT NOT NULL AUTO_INCREMENT COMMENT '候補設備行ID',
  run_id BIGINT NOT NULL COMMENT 'cpsat_runs.id',
  operation_id BIGINT NOT NULL COMMENT 'cpsat_operations.id',
  machine_cd VARCHAR(50) NOT NULL COMMENT '候補設備 k',
  machine_name VARCHAR(100) NULL COMMENT '設備名',
  process_time_sec DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '1本あたり秒（スナップショット）',
  setup_time_sec INT NOT NULL DEFAULT 0 COMMENT '段取秒スナップショット',
  processing_sec INT NOT NULL DEFAULT 0 COMMENT '当該バッチの P_{i,j,k}',
  is_assigned TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'X_{i,j,k}=1',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_cpsat_cand_op_machine (operation_id, machine_cd),
  KEY idx_cpsat_cand_run (run_id, machine_cd),
  CONSTRAINT fk_cpsat_cand_run
    FOREIGN KEY (run_id) REFERENCES cpsat_runs (id) ON DELETE CASCADE,
  CONSTRAINT fk_cpsat_cand_op
    FOREIGN KEY (operation_id) REFERENCES cpsat_operations (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CP-SAT 候補機ドメインと割当 X_{i,j,k}';
