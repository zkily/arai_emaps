-- TABLE: inventory_value_calc_runs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inventory_value_calc_runs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `calc_date` date NOT NULL COMMENT '計算対象日',
  `start_date` date DEFAULT NULL COMMENT '対象期間開始',
  `end_date` date DEFAULT NULL COMMENT '対象期間終了',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '絞込工程 (NULL=全)',
  `total_amount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `material_amount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `component_amount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `stay_amount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `total_rows` int NOT NULL DEFAULT '0',
  `error_rows` int NOT NULL DEFAULT '0',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'completed' COMMENT '状態 (running/completed/failed)',
  `executed_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_calc_run_date` (`calc_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='棚卸金額計算バッチ';

SET FOREIGN_KEY_CHECKS = 1;
