-- TABLE: cpsat_candidates
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `cpsat_candidates` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '候補設備行ID',
  `run_id` bigint NOT NULL COMMENT 'cpsat_runs.id',
  `operation_id` bigint NOT NULL COMMENT 'cpsat_operations.id',
  `machine_cd` varchar(50) NOT NULL COMMENT '候補設備 k',
  `machine_name` varchar(100) DEFAULT NULL COMMENT '設備名',
  `process_time_sec` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '1本あたり秒（スナップショット）',
  `setup_time_sec` int NOT NULL DEFAULT '0' COMMENT '段取秒スナップショット',
  `processing_sec` int NOT NULL DEFAULT '0' COMMENT '当該バッチの P_{i,j,k}',
  `is_assigned` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'X_{i,j,k}=1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cpsat_cand_op_machine` (`operation_id`,`machine_cd`),
  KEY `idx_cpsat_cand_run` (`run_id`,`machine_cd`),
  CONSTRAINT `fk_cpsat_cand_op` FOREIGN KEY (`operation_id`) REFERENCES `cpsat_operations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cpsat_cand_run` FOREIGN KEY (`run_id`) REFERENCES `cpsat_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='CP-SAT 候補機ドメインと割当 X_{i,j,k}';

SET FOREIGN_KEY_CHECKS = 1;
