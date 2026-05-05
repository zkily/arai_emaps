SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for inventory_value_calc_runs
-- ----------------------------
DROP TABLE IF EXISTS `inventory_value_calc_runs`;
CREATE TABLE `inventory_value_calc_runs`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `calc_date` date NOT NULL COMMENT '計算対象日',
  `start_date` date NULL DEFAULT NULL COMMENT '対象期間開始',
  `end_date` date NULL DEFAULT NULL COMMENT '対象期間終了',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '絞込工程 (NULL=全)',
  `total_amount` decimal(18, 2) NOT NULL DEFAULT 0.00,
  `material_amount` decimal(18, 2) NOT NULL DEFAULT 0.00,
  `component_amount` decimal(18, 2) NOT NULL DEFAULT 0.00,
  `stay_amount` decimal(18, 2) NOT NULL DEFAULT 0.00,
  `total_rows` int NOT NULL DEFAULT 0,
  `error_rows` int NOT NULL DEFAULT 0,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'completed' COMMENT '状態 (running/completed/failed)',
  `executed_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_calc_run_date`(`calc_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin COMMENT = '棚卸金額計算バッチ' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of inventory_value_calc_runs
-- ----------------------------
INSERT INTO `inventory_value_calc_runs` VALUES (1, '2026-04-20', '2026-03-01', '2026-03-31', 'KT01', 482334.70, 0.00, 0.00, 482334.70, 38, 1, 'completed', 'zkily', '2026-04-20 17:48:26');
INSERT INTO `inventory_value_calc_runs` VALUES (2, '2026-04-20', '2026-03-01', '2026-03-31', 'KT04', 4292719.16, 0.00, 0.00, 4292719.16, 47, 1, 'completed', 'zkily', '2026-04-20 17:55:40');
INSERT INTO `inventory_value_calc_runs` VALUES (3, '2026-04-20', '2026-03-01', '2026-03-31', NULL, 47516178.38, 0.00, 0.00, 47516178.38, 647, 63, 'completed', 'zkily', '2026-04-20 18:20:19');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
