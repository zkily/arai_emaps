-- TABLE: product_route_step_machines
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_route_step_machines` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `step_no` int NOT NULL,
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `process_time_sec` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '1本あたり加工時間(秒)。バッチ加工時間 P は数量×本秒で算出',
  `setup_time` int NOT NULL DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_step` (`product_cd`,`route_cd`,`step_no`) USING BTREE,
  KEY `idx_machine` (`machine_cd`) USING BTREE,
  CONSTRAINT `product_route_step_machines_ibfk_1` FOREIGN KEY (`machine_cd`) REFERENCES `machines` (`machine_cd`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=DYNAMIC COMMENT='製品別工程ステップ設備';

SET FOREIGN_KEY_CHECKS = 1;
