SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for product_route_steps (製品別工程ルートステップ)
-- ----------------------------
DROP TABLE IF EXISTS `product_route_step_machines`;
DROP TABLE IF EXISTS `product_route_steps`;

CREATE TABLE `product_route_steps` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品CD',
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートCD',
  `step_no` int NOT NULL COMMENT '順番',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '工程CD',
  `machine_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '設備ID',
  `standard_cycle_time` decimal(10, 2) NULL DEFAULT NULL COMMENT '標準サイクルタイム(秒)',
  `setup_time` decimal(10, 2) NULL DEFAULT NULL COMMENT '段取り時間(秒)',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_product_route_step`(`product_cd` ASC, `route_cd` ASC, `step_no` ASC) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 CHARACTER SET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品別工程ルートステップ' ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for product_route_step_machines (製品別工程ステップ設備)
-- ----------------------------
CREATE TABLE `product_route_step_machines` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `step_no` int NOT NULL,
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `process_time_sec` decimal(4, 2) NOT NULL DEFAULT 0.00,
  `setup_time` int NOT NULL DEFAULT 0,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_step`(`product_cd` ASC, `route_cd` ASC, `step_no` ASC) USING BTREE,
  INDEX `idx_machine`(`machine_cd` ASC) USING BTREE,
  CONSTRAINT `product_route_step_machines_ibfk_1` FOREIGN KEY (`machine_cd`) REFERENCES `machines` (`machine_cd`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 CHARACTER SET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品別工程ステップ設備' ROW_FORMAT=DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
