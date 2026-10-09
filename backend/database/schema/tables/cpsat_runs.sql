-- TABLE: cpsat_runs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `cpsat_runs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '求解実行ID',
  `run_code` varchar(40) DEFAULT NULL COMMENT '表示用コード（例: CPSAT-20260904-001）',
  `name` varchar(100) DEFAULT NULL COMMENT '実行名',
  `horizon_start` datetime NOT NULL COMMENT '計画期間開始（S/E の原点）',
  `horizon_end` datetime NOT NULL COMMENT '計画期間終了',
  `time_unit_sec` int NOT NULL DEFAULT '60' COMMENT 'CP-SAT 整数時間の1単位（秒）',
  `objective_type` varchar(20) NOT NULL DEFAULT 'tardiness' COMMENT 'makespan / tardiness / weighted',
  `makespan_weight` decimal(8,4) NOT NULL DEFAULT '0.0000' COMMENT '加重目的の C_max 係数',
  `tardiness_weight` decimal(8,4) NOT NULL DEFAULT '1.0000' COMMENT '加重目的の ΣT_i 係数',
  `max_solve_seconds` int NOT NULL DEFAULT '60' COMMENT 'ソルバ上限秒',
  `status` varchar(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/queued/running/optimal/feasible/infeasible/error/cancelled',
  `solver_status` varchar(40) DEFAULT NULL COMMENT 'OR-Tools 生ステータス',
  `wall_time_sec` decimal(10,3) DEFAULT NULL COMMENT '実求解時間（秒）',
  `makespan_sec` bigint DEFAULT NULL COMMENT 'C_max（秒、horizon_start 起点）',
  `total_tardiness_sec` bigint DEFAULT NULL COMMENT 'Σ T_i（秒）',
  `objective_value` decimal(18,4) DEFAULT NULL COMMENT '目的関数値',
  `job_count` int NOT NULL DEFAULT '0' COMMENT '展開した注文数 i',
  `operation_count` int NOT NULL DEFAULT '0' COMMENT '展開した工程数 (i,j)',
  `error_message` text COMMENT '失敗・実行不能の理由',
  `created_by` varchar(50) DEFAULT NULL COMMENT '実行者',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cpsat_runs_code` (`run_code`),
  KEY `idx_cpsat_runs_status` (`status`),
  KEY `idx_cpsat_runs_horizon` (`horizon_start`,`horizon_end`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='CP-SAT 求解実行ヘッダ';

SET FOREIGN_KEY_CHECKS = 1;
