-- TABLE: inventory_value_calc_details
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inventory_value_calc_details` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `run_id` int NOT NULL COMMENT '計算バッチID',
  `inventory_log_id` int DEFAULT NULL COMMENT '棚卸ログID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `item_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '区分 (材料/部品/ステー)',
  `quantity` decimal(12,4) DEFAULT '0.0000',
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '適用ルートCD',
  `step_no` int DEFAULT NULL COMMENT '適用ステップ',
  `unit_price_snapshot` decimal(18,6) DEFAULT NULL COMMENT 'スナップショット累計単価',
  `amount` decimal(18,2) DEFAULT NULL COMMENT '金額 (数量×単価)',
  `price_rule_id` int DEFAULT NULL COMMENT '適用単価ルールID',
  `error_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'エラーコード (NULL=正常)',
  `error_message` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'エラー内容',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_calc_detail_run` (`run_id`),
  KEY `idx_calc_detail_product` (`product_cd`,`process_cd`),
  CONSTRAINT `fk_calc_detail_run` FOREIGN KEY (`run_id`) REFERENCES `inventory_value_calc_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='棚卸金額計算明細';

SET FOREIGN_KEY_CHECKS = 1;
