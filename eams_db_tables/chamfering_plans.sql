SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for chamfering_plans
-- ----------------------------
DROP TABLE IF EXISTS `chamfering_plans`;
CREATE TABLE `chamfering_plans`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `cutting_management_id` int NULL DEFAULT NULL COMMENT '元切断指示ID（新規追加時はNULL）',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `production_order` int NULL DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int NULL DEFAULT 0 COMMENT '生産数',
  `production_lot_size` int NULL DEFAULT NULL COMMENT 'ロット数',
  `lot_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo',
  `cutting_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長',
  `chamfering_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取長',
  `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード',
  `cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'CD（管理コード後5位）',
  `production_completed` tinyint NULL DEFAULT NULL COMMENT '生産完了',
  `no_count` tinyint NULL DEFAULT NULL COMMENT 'カウント無',
  `has_sw_process` tinyint NULL DEFAULT NULL COMMENT 'SW工程',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_cutting_management_id`(`cutting_management_id` ASC) USING BTREE,
  INDEX `idx_production_month`(`production_month` ASC) USING BTREE,
  INDEX `idx_production_day`(`production_day` ASC) USING BTREE,
  INDEX `idx_production_line`(`production_line` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 653 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '面取バッチ一覧（chamfering_plans）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of chamfering_plans
-- ----------------------------
INSERT INTO `chamfering_plans` VALUES (607, 1471, '2026-05-01', '2026-05-07', '成型18', 4, '91671', 'D54L CTR', 2700, 5, '1', 545.00, 544.50, NULL, '14.0×1.00×5345', '2605916711804-05-01', '05-01', NULL, NULL, 0, '2026-04-24 11:44:09');
INSERT INTO `chamfering_plans` VALUES (608, 1472, '2026-05-01', '2026-05-07', '成型18', 4, '91671', 'D54L CTR', 2700, 5, '2', 545.00, 544.50, NULL, '14.0×1.00×5345', '2605916711804-05-02', '05-02', NULL, NULL, 0, '2026-04-24 11:44:22');
INSERT INTO `chamfering_plans` VALUES (615, 1483, '2026-04-01', '2026-05-07', '成型24', 2, '92671', '655D 3RD SIDE', 1956, 16, '10', 790.50, 790.00, 790.00, '14.0×2.30×4929', '2604926712402-16-10', '16-10', NULL, NULL, 0, '2026-04-24 11:47:15');
INSERT INTO `chamfering_plans` VALUES (619, 1495, '2026-04-01', '2026-05-07', '成型24', 2, '92671', '655D 3RD SIDE', 1956, 16, '11', 790.50, 790.00, 790.00, '14.0×2.30×4929', '2604926712402-16-11', '16-11', NULL, NULL, 0, '2026-04-27 09:16:49');
INSERT INTO `chamfering_plans` VALUES (627, 1503, '2026-05-01', '2026-05-07', '成型15', 7, '92601', '554D SD', 2608, 2, '1', 549.00, 548.50, 546.00, '14.0×2.30×4929', '2605926011507-02-01', '02-01', NULL, NULL, 1, '2026-04-27 09:53:03');
INSERT INTO `chamfering_plans` VALUES (628, 1504, '2026-05-01', '2026-05-07', '成型15', 7, '92601', '554D SD', 2608, 2, '2', 549.00, 548.50, 546.00, '14.0×2.30×4929', '2605926011507-02-02', '02-02', NULL, NULL, 1, '2026-04-27 09:53:08');
INSERT INTO `chamfering_plans` VALUES (629, 1505, '2026-05-01', '2026-05-07', '成型14', 6, '92161', '3V0 FR プレート', 1800, 3, '1', 767.20, 766.70, 766.00, '14.0×1.50×4680', '2605921611406-03-01', '03-01', NULL, NULL, 1, '2026-04-27 09:53:22');
INSERT INTO `chamfering_plans` VALUES (630, 1506, '2026-05-01', '2026-05-07', '成型14', 6, '92161', '3V0 FR プレート', 1800, 3, '2', 767.20, 766.70, 766.00, '14.0×1.50×4680', '2605921611406-03-02', '03-02', NULL, NULL, 1, '2026-04-27 09:53:32');
INSERT INTO `chamfering_plans` VALUES (635, 1511, '2026-05-01', '2026-05-07', '成型09', 2, '91181', 'X61G 3RD', 1500, 2, '1', 1249.50, 1248.00, 0.00, '12.7×2.00×4000', '2605911810902-02-01', '02-01', NULL, NULL, 0, '2026-04-27 09:55:21');
INSERT INTO `chamfering_plans` VALUES (636, 1512, '2026-05-01', '2026-05-07', '成型09', 2, '91181', 'X61G 3RD', 1500, 2, '2', 1249.50, 1248.00, 0.00, '12.7×2.00×4000', '2605911810902-02-02', '02-02', NULL, NULL, 0, '2026-04-27 09:55:24');
INSERT INTO `chamfering_plans` VALUES (641, 1524, '2026-04-01', '2026-05-07', '成型05', 1, '92221', '900B FR', 2282, 4, '1', 778.00, 777.50, 774.50, '14.0×2.30×5526', '2604922210501-04-01', '04-01', NULL, NULL, 0, '2026-04-27 16:33:39');
INSERT INTO `chamfering_plans` VALUES (642, 1525, '2026-04-01', '2026-05-07', '成型05', 1, '92221', '900B FR', 2282, 4, '2', 778.00, 777.50, 774.50, '14.0×2.30×5526', '2604922210501-04-02', '04-02', NULL, NULL, 0, '2026-04-27 16:33:42');
INSERT INTO `chamfering_plans` VALUES (643, 1526, '2026-04-01', '2026-05-07', '成型04', 1, '91441', '400B FR', 2282, 8, '5', 778.00, 777.50, 774.50, '14.0×1.35×5525', '2604914410401-08-05', '08-05', NULL, NULL, 0, '2026-04-27 16:33:57');
INSERT INTO `chamfering_plans` VALUES (644, 1527, '2026-04-01', '2026-05-07', '成型04', 1, '91441', '400B FR', 2282, 8, '6', 778.00, 777.50, 774.50, '14.0×1.35×5525', '2604914410401-08-06', '08-06', NULL, NULL, 0, '2026-04-27 16:34:04');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
