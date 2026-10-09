-- TABLE: cpsat_jobs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `cpsat_jobs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ジョブ行ID',
  `run_id` bigint NOT NULL COMMENT 'cpsat_runs.id',
  `job_index` int NOT NULL COMMENT '注文インデックス i',
  `source_type` varchar(32) NOT NULL COMMENT 'order_daily / production_schedule / manual',
  `source_id` int DEFAULT NULL COMMENT '元レコードID',
  `order_no` varchar(50) DEFAULT NULL COMMENT '表示用受注番号',
  `product_cd` varchar(50) NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) DEFAULT NULL COMMENT '製品名',
  `q_target` int NOT NULL COMMENT '最終入库量 Q_target',
  `q_start` int NOT NULL COMMENT '切断投入量 Q_start = Q_target / Π Y_j',
  `lot_size` int NOT NULL DEFAULT '0' COMMENT '製品ロットサイズ（本）。1以下は未分割',
  `lot_index` int NOT NULL DEFAULT '1' COMMENT '当該日・製品内のロット番号（1始まり）',
  `lot_count` int NOT NULL DEFAULT '1' COMMENT '当該日・製品のロット数',
  `due_at` datetime DEFAULT NULL COMMENT '約束交期 D_i',
  `due_sec` int DEFAULT NULL COMMENT 'D_i（horizon 起点秒）',
  `last_op_end_sec` int DEFAULT NULL COMMENT '最終工程終了 E_{i,last}',
  `tardiness_sec` int DEFAULT NULL COMMENT '遅延 T_i = max(0, E_last - D_i)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cpsat_jobs_run_index` (`run_id`,`job_index`),
  KEY `idx_cpsat_jobs_product` (`run_id`,`product_cd`),
  KEY `idx_cpsat_jobs_source` (`source_type`,`source_id`),
  CONSTRAINT `fk_cpsat_jobs_run` FOREIGN KEY (`run_id`) REFERENCES `cpsat_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='CP-SAT 注文ジョブ i（実行時スナップショット）';

SET FOREIGN_KEY_CHECKS = 1;
