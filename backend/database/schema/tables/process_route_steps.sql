-- TABLE: process_route_steps
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `process_route_steps` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ルートステップID',
  `route_cd` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートID',
  `step_no` int NOT NULL COMMENT 'ステップ番号',
  `process_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '工程ID',
  `yield_percent` decimal(5,2) DEFAULT '100.00' COMMENT '歩留率（%）',
  `cycle_sec` decimal(5,2) DEFAULT '0.00' COMMENT '標準サイクル（秒）',
  `wait_sec_after` int NOT NULL DEFAULT '0' COMMENT '後工程開始までの最小待ち秒（T_wait）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
