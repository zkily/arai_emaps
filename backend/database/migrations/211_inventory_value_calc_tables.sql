-- 棚卸金額計算バッチ・明細スナップショット
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inventory_value_calc_runs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `calc_date` date NOT NULL COMMENT '計算対象日',
  `start_date` date DEFAULT NULL COMMENT '対象期間開始',
  `end_date` date DEFAULT NULL COMMENT '対象期間終了',
  `process_cd` varchar(50) DEFAULT NULL COMMENT '絞込工程 (NULL=全)',
  `total_amount` decimal(18,2) NOT NULL DEFAULT 0.00,
  `material_amount` decimal(18,2) NOT NULL DEFAULT 0.00,
  `component_amount` decimal(18,2) NOT NULL DEFAULT 0.00,
  `stay_amount` decimal(18,2) NOT NULL DEFAULT 0.00,
  `total_rows` int NOT NULL DEFAULT 0,
  `error_rows` int NOT NULL DEFAULT 0,
  `status` varchar(20) NOT NULL DEFAULT 'completed' COMMENT '状態 (running/completed/failed)',
  `executed_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_calc_run_date` (`calc_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='棚卸金額計算バッチ';

CREATE TABLE IF NOT EXISTS `inventory_value_calc_details` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `run_id` int NOT NULL COMMENT '計算バッチID',
  `inventory_log_id` int DEFAULT NULL COMMENT '棚卸ログID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `item_type` varchar(30) DEFAULT NULL COMMENT '区分 (材料/部品/ステー)',
  `quantity` decimal(12,4) DEFAULT 0.0000,
  `route_cd` varchar(50) DEFAULT NULL COMMENT '適用ルートCD',
  `step_no` int DEFAULT NULL COMMENT '適用ステップ',
  `unit_price_snapshot` decimal(18,6) DEFAULT NULL COMMENT 'スナップショット累計単価',
  `amount` decimal(18,2) DEFAULT NULL COMMENT '金額 (数量×単価)',
  `price_rule_id` int DEFAULT NULL COMMENT '適用単価ルールID',
  `error_code` varchar(50) DEFAULT NULL COMMENT 'エラーコード (NULL=正常)',
  `error_message` varchar(500) DEFAULT NULL COMMENT 'エラー内容',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_calc_detail_run` (`run_id`),
  KEY `idx_calc_detail_product` (`product_cd`, `process_cd`),
  CONSTRAINT `fk_calc_detail_run` FOREIGN KEY (`run_id`) REFERENCES `inventory_value_calc_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='棚卸金額計算明細';

SET FOREIGN_KEY_CHECKS = 1;
