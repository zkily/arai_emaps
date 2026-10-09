-- TABLE: product_route_steps
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_route_steps` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品CD',
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートCD',
  `step_no` int NOT NULL COMMENT '順番',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '工程CD',
  `yield_percent` decimal(5,2) DEFAULT NULL COMMENT '歩留(%)。NULL時は工程ルート/工程マスタ',
  `wait_sec_after` int DEFAULT NULL COMMENT '後工程開始までの最小待ち秒。NULL時は工程ルート既定',
  `machine_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '設備ID',
  `standard_cycle_time` decimal(10,2) DEFAULT NULL COMMENT '標準サイクルタイム(秒)',
  `setup_time` decimal(10,2) DEFAULT NULL COMMENT '段取り時間(秒)',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '備考',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uq_product_route_step` (`product_cd`,`route_cd`,`step_no`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=DYNAMIC COMMENT='製品別工程ルートステップ';

SET FOREIGN_KEY_CHECKS = 1;
