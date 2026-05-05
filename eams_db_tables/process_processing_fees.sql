SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for process_processing_fees
-- ----------------------------
DROP TABLE IF EXISTS `process_processing_fees`;
CREATE TABLE `process_processing_fees`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '工程CD（processes.process_cd）',
  `method_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '加工方法コード',
  `method_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '加工方法名称',
  `unit_price` decimal(18, 4) NOT NULL DEFAULT 0.0000 COMMENT '加工費単価',
  `currency` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'JPY' COMMENT '通貨',
  `charge_uom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '式' COMMENT '課金単位（式/個/H 等）',
  `effective_from` date NULL DEFAULT NULL COMMENT '有効開始',
  `effective_to` date NULL DEFAULT NULL COMMENT '有効終了',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'active' COMMENT '状態 active/historical',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_ppf_process`(`process_cd` ASC) USING BTREE,
  INDEX `idx_ppf_process_method`(`process_cd` ASC, `method_cd` ASC) USING BTREE,
  INDEX `idx_ppf_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 29 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin COMMENT = '工程加工費マスタ' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of process_processing_fees
-- ----------------------------
INSERT INTO `process_processing_fees` VALUES (1, 'KT01', 'cut-001', '通常切断', 3.5400, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:08:57', '2026-04-09 13:08:57');
INSERT INTO `process_processing_fees` VALUES (2, 'KT01', 'cut-002', '通常切断', 3.9000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:09:32', '2026-04-09 13:09:32');
INSERT INTO `process_processing_fees` VALUES (3, 'KT01', 'cut-003', '通常切断', 3.9500, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:10:05', '2026-04-09 13:10:05');
INSERT INTO `process_processing_fees` VALUES (4, 'KT01', 'cut-004', '通常切断', 4.3000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:10:20', '2026-04-09 13:10:20');
INSERT INTO `process_processing_fees` VALUES (5, 'KT01', 'cut-005', '通常切断', 4.4300, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:10:42', '2026-04-09 13:10:42');
INSERT INTO `process_processing_fees` VALUES (6, 'KT01', 'cut-006', '通常切断', 4.5000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:12:45', '2026-04-09 13:12:45');
INSERT INTO `process_processing_fees` VALUES (7, 'KT01', 'cut-007', '通常切断', 5.0000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:13:15', '2026-04-09 13:13:15');
INSERT INTO `process_processing_fees` VALUES (8, 'KT01', 'cut-008', '通常切断', 6.0000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:13:36', '2026-04-09 13:13:36');
INSERT INTO `process_processing_fees` VALUES (9, 'KT01', 'cut-009', '通常切断', 7.0000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:13:55', '2026-04-09 13:13:55');
INSERT INTO `process_processing_fees` VALUES (10, 'KT01', 'cut-010', '通常切断', 7.5000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:14:15', '2026-04-09 13:14:15');
INSERT INTO `process_processing_fees` VALUES (11, 'KT02', 'cha-001', '面取', 2.7000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:17:01', '2026-04-09 13:17:01');
INSERT INTO `process_processing_fees` VALUES (12, 'KT02', 'cha-002', '面取', 3.0000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:17:21', '2026-04-09 13:17:51');
INSERT INTO `process_processing_fees` VALUES (13, 'KT02', 'cha-003', '面取', 3.7700, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:17:35', '2026-04-09 13:17:35');
INSERT INTO `process_processing_fees` VALUES (14, 'KT02', 'cha-004', '面取', 3.8800, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:19:58', '2026-04-09 13:20:30');
INSERT INTO `process_processing_fees` VALUES (15, 'KT02', 'cha-005', '面取', 4.2800, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:20:25', '2026-04-09 13:20:25');
INSERT INTO `process_processing_fees` VALUES (16, 'KT02', 'cha-006', '面取', 6.0000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:21:01', '2026-04-09 13:21:01');
INSERT INTO `process_processing_fees` VALUES (17, 'KT02', 'cha-007', '面取', 6.1300, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:21:26', '2026-04-09 13:21:26');
INSERT INTO `process_processing_fees` VALUES (18, 'KT02', 'cha-008', '面取', 6.2700, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:21:45', '2026-04-09 13:21:45');
INSERT INTO `process_processing_fees` VALUES (19, 'KT02', 'cha-009', '面取', 6.3000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:22:06', '2026-04-09 13:22:06');
INSERT INTO `process_processing_fees` VALUES (20, 'KT02', 'cha-010', '面取', 7.5000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:22:28', '2026-04-09 13:22:28');
INSERT INTO `process_processing_fees` VALUES (21, 'KT02', 'cha-011', '面取', 7.5200, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:22:42', '2026-04-09 13:22:42');
INSERT INTO `process_processing_fees` VALUES (22, 'KT02', 'cha-012', '面取', 7.6600, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:22:58', '2026-04-09 13:22:58');
INSERT INTO `process_processing_fees` VALUES (23, 'KT02', 'cha-013', '面取', 8.0300, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:23:19', '2026-04-09 13:23:19');
INSERT INTO `process_processing_fees` VALUES (24, 'KT02', 'cha-014', '面取', 8.3200, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:23:37', '2026-04-09 13:23:37');
INSERT INTO `process_processing_fees` VALUES (25, 'KT02', 'cha-015', '面取', 8.5000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:23:54', '2026-04-09 13:23:54');
INSERT INTO `process_processing_fees` VALUES (26, 'KT02', 'cha-016', '面取', 9.0000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:24:13', '2026-04-09 13:24:13');
INSERT INTO `process_processing_fees` VALUES (27, 'KT02', 'cha-017', '面取', 10.4500, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:24:43', '2026-04-09 13:24:43');
INSERT INTO `process_processing_fees` VALUES (28, 'KT02', 'cha-018', '面取', 24.6000, 'JPY', '式', '2026-04-01', '2030-03-31', 'active', '', 'zkily', 'zkily', '2026-04-09 13:24:57', '2026-04-09 13:24:57');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
