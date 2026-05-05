SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for product_process_bom
-- ----------------------------
DROP TABLE IF EXISTS `product_process_bom`;
CREATE TABLE `product_process_bom`  (
  `product_cd` int NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品名',
  `min_stock_days` int NULL DEFAULT NULL COMMENT '最低在庫日数',
  `safety_stock_days` int NULL DEFAULT NULL COMMENT '安全在庫日数',
  `material_process` tinyint(1) NULL DEFAULT NULL COMMENT '材料 (工程)',
  `material_process_lt` int NULL DEFAULT NULL COMMENT '材料工程LT',
  `cuting_process` tinyint(1) NULL DEFAULT NULL COMMENT '切断 (工程)',
  `cuting_process_lt` int NULL DEFAULT NULL COMMENT '切断工程LT',
  `chamfering_process` tinyint(1) NULL DEFAULT NULL COMMENT '面取 (工程)',
  `chamfering_process_lt` int NULL DEFAULT NULL COMMENT '面取工程LT',
  `swaging_process` tinyint(1) NULL DEFAULT NULL COMMENT 'SW (工程)',
  `swaging_process_lt` int NULL DEFAULT NULL COMMENT 'SW工程LT',
  `forming_process` tinyint(1) NULL DEFAULT NULL COMMENT '成型 (工程)',
  `forming_process_lt` int NULL DEFAULT NULL COMMENT '成型工程LT',
  `plating_process` tinyint(1) NULL DEFAULT NULL COMMENT 'メッキ (工程)',
  `plating_process_lt` int NULL DEFAULT NULL COMMENT 'メッキ工程LT',
  `outsourced_plating_process` tinyint(1) NULL DEFAULT NULL COMMENT '外注メッキ (工程)',
  `outsourced_plating_process_lt` int NULL DEFAULT NULL COMMENT '外注メッキ工程LT',
  `welding_process` tinyint(1) NULL DEFAULT NULL COMMENT '溶接 (工程)',
  `welding_process_lt` int NULL DEFAULT NULL COMMENT '溶接工程LT',
  `outsourced_welding_process` tinyint(1) NULL DEFAULT NULL COMMENT '外注溶接 (工程)',
  `outsourced_welding_process_lt` int NULL DEFAULT NULL COMMENT '外注溶接工程LT',
  `inspection_process` tinyint(1) NULL DEFAULT NULL COMMENT '検査 (工程)',
  `inspection_process_lt` int NULL DEFAULT NULL COMMENT '検査工程LT',
  `outsourced_warehouse_process` tinyint(1) NULL DEFAULT NULL COMMENT '外注倉庫 (工程)',
  `outsourced_warehouse_process_lt` int NULL DEFAULT NULL COMMENT '外注検査工程LT',
  `pre_plating_welding` tinyint(1) NULL DEFAULT NULL COMMENT 'メッキ前溶接 (工程)',
  `post_inspection_welding` tinyint(1) NULL DEFAULT NULL COMMENT '検査後溶接 (工程)',
  `post_inspection_welding_lt` int NULL DEFAULT NULL COMMENT '検査後溶接工程LT',
  `is_discontinued` tinyint(1) NULL DEFAULT NULL COMMENT '終息',
  PRIMARY KEY (`product_cd`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '製品工程BOM (Product Process BOM)' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of product_process_bom
-- ----------------------------
INSERT INTO `product_process_bom` VALUES (90011, '011B CTR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90012, '240B CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90021, '208W(485L)', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90041, '030L FR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90061, '080A FR1', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90071, '320B CTR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90091, '090A CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90141, '140A CTR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90142, '200B CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90151, '140A RR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90161, '141A CTR', 1, 10, 1, 11, 1, 10, 1, 9, 0, NULL, 1, 6, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90191, '200B(123A) RR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90201, '215L CTR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90221, '220B CTR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90231, '220B RR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90271, '3X45 CTR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90281, '3X45 FR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90291, '3X45 SIDE', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90301, '3X45 対米 FR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90311, '3X45 対米 SIDE', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90321, '400A CTR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90331, '400A SD', 1, 9, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 1, 6, 0, NULL, 1, 3, 0, NULL, 1, 1, 0, NULL, 0, 1, 2, 0);
INSERT INTO `product_process_bom` VALUES (90341, '400A FR ノーマル', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90351, '400A RR', 2, 10, 1, 11, 1, 9, 0, NULL, 0, NULL, 1, 7, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90371, '421 FR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90411, '453A CTR アーチ', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90441, '480L CTR', NULL, 11, 1, 11, 0, NULL, 1, 9, 0, NULL, 1, 6, 1, 5, 0, NULL, 1, 3, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90471, '4B45X FR', 2, 11, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (90481, '4X45 RR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90491, '540A 3RD', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90501, '540A FR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90511, '540A RR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90521, '540A アーチ', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90571, '590L 固定', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (90591, '610L 3RD', 2, 11, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (90611, '610L WF', 2, 11, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (90631, '610L タンブル', 2, 10, 1, 10, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90633, '400B FR スロープ', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90661, '668A 130P', 2, 10, 1, 11, 1, 10, 1, 9, 0, NULL, 1, 6, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90681, '668A 80P', 2, 10, 1, 11, 1, 10, 1, 9, 0, NULL, 1, 6, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90711, '720A SD', 1, 11, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 1, 6, 0, NULL, 1, 3, 0, NULL, 1, 1, 0, NULL, 0, 1, 2, 0);
INSERT INTO `product_process_bom` VALUES (90741, '740A RR', 2, 11, 1, 10, 1, 9, 0, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90743, '011B RR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90761, '780A 3RD', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90762, '453A 3RD', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90771, '780A RR', 2, 11, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90791, '805A FR', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (90841, '868N FR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90921, 'BF4 CTR JP', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90931, 'NB8 US EURO', 2, 9, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90932, 'BF4 SIDE EURO', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90941, 'BF4 SIDE JP', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90951, 'C53D 欧州', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90961, 'C53D 標準', 2, 9, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90981, 'FE-5', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (90991, 'FE-7', 2, 11, 1, 12, NULL, NULL, 1, 10, 0, NULL, 1, 7, 0, NULL, 1, 6, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91001, 'HR3 ENCAP', 2, 9, 1, 12, 1, 10, 0, NULL, 0, NULL, 1, 8, 0, NULL, 1, 7, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91002, 'HR3 ENCAP 群馬', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91011, 'HR3 JP', 2, 9, 1, 12, 1, 10, 0, NULL, 0, NULL, 1, 8, 0, NULL, 1, 7, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91012, 'HR3 JP 別注', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91013, 'HR3 JP 群馬', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91021, 'IW-187', 1, 11, 1, 9, 0, NULL, 0, NULL, 0, NULL, 1, 5, 0, NULL, 1, 7, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91111, 'TTA', 0, 8, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 0, NULL, 1, 4, 0, NULL, 1, 5, 1, 1, 0, NULL, 1, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91121, 'TTA Long', 2, 11, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 0, NULL, 1, 4, 1, 2, 1, 5, 1, 1, 0, NULL, 1, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (91151, 'X11M FR', 2, 11, 1, 12, 1, 9, 0, NULL, 0, NULL, 1, 7, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91181, 'X61G 3RD', 0, 11, 1, 11, 1, 10, 1, 9, 0, NULL, 1, 6, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91191, 'X61G FR DISP', 0, 11, 1, 11, 1, 10, 1, 9, 0, NULL, 1, 6, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (91201, 'ACTUATER', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91251, '164B FR', 2, 7, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91252, '240B FR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91253, 'BY2 FR1', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91254, '567D FR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91261, '164B RR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91262, '100B RR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91271, '100B CTR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91301, '240B SD', 1, 7, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 1, 6, 0, NULL, 1, 3, 0, NULL, 1, 1, 0, NULL, 0, 1, 2, 0);
INSERT INTO `product_process_bom` VALUES (91302, '700B SD', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91303, '800B SD', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91304, '014(240)B SD', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91311, '310B CTR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91321, 'XC2A RR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91331, 'XC2A FR', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91351, 'TTA 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91401, '152B RR (150)', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91411, '180B FR', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91412, '180B FR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91441, '400B FR', 2, 8, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91442, '032D FR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91443, 'BY2 FR2', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91444, '753D FR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91451, '400B RR', 1, 7, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91461, '400B CTR', 2, 7, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91471, '190B CTR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 1, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91481, '190B RR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91491, 'TKR FR', 0, 9, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 0, NULL, 1, 4, 0, NULL, 1, 5, 1, 1, 0, NULL, 1, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91511, 'TYF  TI', 2, 11, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 1, 6, 0, NULL, 1, 3, 0, NULL, 1, 1, 0, NULL, 0, 1, NULL, 1);
INSERT INTO `product_process_bom` VALUES (91521, '826B 料金トレー', 2, 9, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91551, 'TKR 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91561, '692B RR', 2, 11, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91571, '750B CTR', 1, 12, 1, 10, 1, 8, 0, NULL, 0, NULL, 1, 6, 1, 7, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (91581, 'D01L RR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91591, 'モニートクッション', 0, 3, 1, 9, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91601, 'XC2B FR LH', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (91611, 'XC2B FR RH', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (91621, 'RE7 CTR', 2, 9, 1, 12, 1, 11, 1, 10, 0, NULL, 1, 7, 0, NULL, 1, 6, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91631, '5A45 FR', 1, 9, 1, 11, 1, 9, 0, NULL, 0, NULL, 1, 7, 0, NULL, 1, 4, 1, 6, 0, NULL, 1, 1, 0, NULL, 1, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91671, 'D54L CTR', 2, 11, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91681, 'D54L RR', 2, 9, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91711, '581B RR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91721, '400B レッグ LH', 1, 18, 1, 9, 0, NULL, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91731, '400B レッグ RH', 1, 18, 1, 9, 0, NULL, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91741, 'B13B FR', 2, 9, 1, 11, 1, 10, 1, 9, 0, NULL, 1, 6, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91751, '570B FR', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91771, '4X45 21MY', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91781, 'MS2 FR', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91791, 'GC7 CTR', 1, 14, 1, 11, 1, 9, 0, NULL, 0, NULL, 1, 7, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91811, '3MO CTR', 1, 10, 1, 11, 1, 7, 0, NULL, 0, NULL, 1, 6, 0, NULL, 1, 4, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91821, '3MO SIDE', 1, 11, 1, 12, 1, 11, 1, 10, 0, NULL, 1, 7, 0, NULL, 1, 4, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (91831, '3N0 RR EU', 2, 9, 1, 11, 1, 8, 0, NULL, 0, NULL, 1, 6, 0, NULL, 1, 4, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91841, '700B CTR 64', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91851, '700B CTR 424', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91861, '3V0 FR MASS', 2, 10, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 0, NULL, 1, 5, 1, 6, 0, NULL, 1, 1, 0, NULL, 1, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91871, '490B RR', 2, 11, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (91881, '800B CTR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91882, '800B CTR 九州', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91891, '202B', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91901, '670B CAP', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91902, '670B RR1 CAP', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91911, '670B 2ND SIDE', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91931, '670B 3RD SIDE', 1, 9, 1, 10, 1, 8, 0, NULL, 0, NULL, 1, 6, 1, 3, 0, NULL, 1, 5, 0, NULL, 1, 1, 0, NULL, 1, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91941, '670B 3RD CTR', 1, 9, 1, 12, 1, 11, 1, 10, 1, NULL, 1, 7, 1, 5, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91942, '670B 3RD CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91951, '961B CTR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91952, '961B CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91953, '961B CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (91981, '5A45 FR DOM', 2, 11, 1, 11, 1, 9, 0, NULL, 0, NULL, 1, 7, 0, NULL, 1, 4, 1, 6, 0, NULL, 1, 1, 0, NULL, 1, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (92001, '840B SIDE', 2, 9, 1, 10, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92011, '840B 2ND CTR', 2, 9, 1, 11, 1, 10, 1, 9, 1, 8, 1, 6, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92021, '840B CTR', 1, 9, 1, 10, 1, 10, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92031, '840B 3RD', 1, 9, 1, 11, 1, 10, 1, 9, 1, 8, 1, 6, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92041, '720B RR SD', 1, 11, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 1, 6, 0, NULL, 1, 3, 0, NULL, 1, 1, 0, NULL, 0, 1, 2, 0);
INSERT INTO `product_process_bom` VALUES (92051, '670B 2ND CTR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92071, '030A SIDE', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92081, '032D RR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92091, '900B 対米', 0, 11, 1, 12, 1, 10, 0, NULL, 0, NULL, 1, 8, 0, NULL, 1, 5, 0, NULL, 0, NULL, 0, NULL, 1, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92101, '900B CTR', 1, 9, 1, 11, 1, 9, 0, NULL, 0, NULL, 1, 7, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92111, '990B RR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92121, '990B CTR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92122, '735D CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92131, '032D CTR', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92141, '300D RR', 2, 7, 1, 11, 1, 10, 0, 9, 0, NULL, 1, 6, 1, 3, 0, NULL, 1, 5, 0, NULL, 1, 1, 0, NULL, 1, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92151, '300D CTR', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92161, '3V0 FR プレート', 2, 10, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 0, NULL, 1, 5, 1, 6, 0, NULL, 1, 1, 0, NULL, 1, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92181, '050D CTR', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92191, '202B FR US', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92201, '970B 3RD', 2, 8, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92211, '960B FR2', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92221, '900B FR', 0, 11, 1, 13, 1, 12, 1, 11, 0, NULL, 1, 8, 0, NULL, 1, 5, 0, NULL, 0, NULL, 0, NULL, 1, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92222, '240B FR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92231, '900B RR', 0, 11, 1, 13, 1, 12, 0, 11, 0, NULL, 1, 8, 0, NULL, 1, 5, 0, NULL, 0, NULL, 0, NULL, 1, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92241, '120D 3RD', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92251, '900B FR 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92261, '900B RR 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92271, '900B 対米 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92281, '091D FR', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92291, '091D CTR', 2, 9, 1, 11, 1, 9, 0, NULL, 0, NULL, 1, 7, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92292, '091D CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92301, '050D RR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92311, 'D89L RR', 2, 11, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (92321, '960B FR1', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92331, '960B RR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92332, '960B RR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92341, 'D70B RR', 2, 11, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (92351, 'D70B CTR', 2, 11, 1, 11, 1, 10, 1, 9, 0, NULL, 1, 6, 1, 4, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (92371, '440D CTR', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92381, '5A45 X1', 2, 8, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92391, '5A45 V2', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92401, '3BV FR', 2, 10, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 0, NULL, 1, 4, 0, NULL, 1, 5, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92411, 'P13C RR', 2, 9, 1, 10, 1, 9, 1, 8, 1, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92421, 'P13C CTR', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92431, '410D RR', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 6, 0, NULL, 1, 5, 0, NULL, 0, NULL, 0, 1, 1, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92441, '310D CTR', 2, 7, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92442, '311D CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92451, '567D CTR', 2, 9, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92461, '524D FR', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92471, '743D FR', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92481, '155D RR', 2, 7, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92491, '3BV FR 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92501, '665D CTR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92511, 'NB8 US', 2, 9, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92521, 'X11M FR1', 2, 11, 1, 12, 1, 9, 0, NULL, 0, NULL, 1, 7, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92531, 'X11M FR2', 2, 11, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92541, '410D FR2', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 0, NULL, 1, 5, 0, NULL, 0, NULL, 0, 1, 1, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92551, 'BY2 CTR', 2, 9, 1, 10, 1, 9, 1, 8, 0, NULL, 1, 6, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92561, 'P13C FR SPK', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 4, 0, NULL, 1, 3, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 1);
INSERT INTO `product_process_bom` VALUES (92571, 'P13C FR', 2, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92581, '554D FR', 2, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92591, '554D CTR', 2, 10, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92601, '554D SD', 1, 9, 1, 12, 1, 11, 1, 10, 1, 9, 1, 7, 1, 6, 0, NULL, 1, 3, 0, NULL, 1, 1, 0, NULL, 0, 1, 2, 0);
INSERT INTO `product_process_bom` VALUES (92611, '500D CTR', 2, 9, 1, 10, 1, 10, 1, 9, 1, 7, 1, 6, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92621, '410D FR1 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92631, '410D FR2 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92641, '410D CTR 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92651, '500D RR', 2, 9, 1, 10, 1, 10, 1, 9, 0, NULL, 1, 6, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92652, '500D RR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92661, 'CH2 RR', 2, 10, 1, 10, 1, 8, 0, NULL, 0, NULL, 1, 6, 0, NULL, 1, 5, 1, 4, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92671, '655D 3RD SIDE', NULL, 10, 0, NULL, 1, 9, 1, 8, 0, NULL, 1, 5, 1, 3, 0, NULL, 1, 4, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92681, '450D FR', NULL, NULL, 0, NULL, 1, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92691, '655D 3RD CTR', NULL, 10, 0, NULL, 1, 9, 1, 8, 1, 7, 1, 5, 1, 3, 0, NULL, 1, 2, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92701, '450D RR', NULL, NULL, 0, NULL, 1, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92702, '450D RR 旧品', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92711, '155D FR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92721, '706D CTR', 2, 7, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92731, '740D RR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92741, '740D CTR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92751, '410D FR1', NULL, 10, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 0, NULL, 1, 5, 0, NULL, 0, NULL, 0, NULL, 1, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92761, '410D RR 加工品', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92771, '670B RR1 CAP', 2, 7, 1, 9, 1, 7, 0, NULL, 0, NULL, 1, 5, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92781, '410D CTR', NULL, 9, 1, 10, 1, 9, 1, 8, 1, 7, 1, 5, 1, NULL, 1, 5, 0, NULL, 0, NULL, 0, NULL, 1, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92791, '737D RR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92801, '737D CTR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92811, '737D 3RD', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92821, '699D RR', 2, 7, 1, 8, 1, 7, 0, NULL, 0, NULL, 1, 4, 1, 2, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92831, '310D FR', NULL, NULL, 0, NULL, 1, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92841, 'C53L 27MY', NULL, 0, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92851, '800D FR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92861, '805D FR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92871, '740D FR', NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92881, '836D RR', 2, 7, 1, 9, 1, 8, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92891, '836D CTR', 2, 7, 1, 9, 1, 8, 0, NULL, 0, NULL, 1, 5, 1, 3, 0, NULL, 0, NULL, 0, NULL, 1, 1, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92901, '807D FR', NULL, NULL, 0, NULL, NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, 0, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92911, '805D RR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92921, '695D CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92931, '3W0S FR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92941, '695D SD', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92951, '611D RR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92961, '611D CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92971, '692D FR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);
INSERT INTO `product_process_bom` VALUES (92981, '800D CTR', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0);

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
