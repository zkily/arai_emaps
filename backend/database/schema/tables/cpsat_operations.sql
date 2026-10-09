-- TABLE: cpsat_operations
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `cpsat_operations` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '工程行ID',
  `run_id` bigint NOT NULL COMMENT 'cpsat_runs.id',
  `job_id` bigint NOT NULL COMMENT 'cpsat_jobs.id',
  `op_index` int NOT NULL COMMENT '工程インデックス j',
  `step_no` int NOT NULL COMMENT '製品ルート step_no',
  `process_cd` varchar(20) NOT NULL COMMENT '工程CD',
  `process_name` varchar(60) DEFAULT NULL COMMENT '工程名',
  `yield_percent` decimal(5,2) NOT NULL DEFAULT '100.00' COMMENT 'スナップショット歩留 Y_j（%）',
  `wait_sec_after` int NOT NULL DEFAULT '0' COMMENT '後工程への T_wait（秒）',
  `q_input` int NOT NULL DEFAULT '0' COMMENT '当該工程投入量 Q_j',
  `q_output` int NOT NULL DEFAULT '0' COMMENT '歩留後出来高',
  `start_sec` int DEFAULT NULL COMMENT '開始 S_{i,j}（horizon 起点秒）',
  `end_sec` int DEFAULT NULL COMMENT '終了 E_{i,j}',
  `start_at` datetime DEFAULT NULL COMMENT '開始日時',
  `end_at` datetime DEFAULT NULL COMMENT '終了日時',
  `assigned_machine_cd` varchar(50) DEFAULT NULL COMMENT '割当設備 k（X=1 の機）',
  `assigned_machine_name` varchar(100) DEFAULT NULL COMMENT '割当設備名',
  `processing_sec` int DEFAULT NULL COMMENT '選択機のバッチ加工時間 P',
  `setup_sec` int DEFAULT NULL COMMENT '段取秒',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cpsat_ops_job_index` (`job_id`,`op_index`),
  KEY `idx_cpsat_ops_run` (`run_id`,`process_cd`),
  KEY `idx_cpsat_ops_machine` (`run_id`,`assigned_machine_cd`,`start_sec`),
  CONSTRAINT `fk_cpsat_ops_job` FOREIGN KEY (`job_id`) REFERENCES `cpsat_jobs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cpsat_ops_run` FOREIGN KEY (`run_id`) REFERENCES `cpsat_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='CP-SAT 工程 j（S/E と割当結果）';

SET FOREIGN_KEY_CHECKS = 1;
