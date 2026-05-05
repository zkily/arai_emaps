SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for product_bom_lines
-- ----------------------------
DROP TABLE IF EXISTS `product_bom_lines`;
CREATE TABLE `product_bom_lines`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `header_id` int NOT NULL COMMENT 'ヘッダID',
  `parent_line_id` int NULL DEFAULT NULL COMMENT '親行ID (多階層)',
  `line_no` int NOT NULL DEFAULT 10 COMMENT '行番号',
  `component_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'material' COMMENT '子品目種別 (material/purchased/subassy/phantom)',
  `component_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '子品目の製品CD',
  `component_material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '子品目の材料CD',
  `qty_per` decimal(12, 6) NOT NULL DEFAULT 1.000000 COMMENT '親1基準あたり所要量',
  `uom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '個' COMMENT '単位',
  `scrap_rate` decimal(5, 2) NULL DEFAULT 0.00 COMMENT 'スクラップ率 (%)',
  `consume_process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '投入工程CD',
  `consume_step_no` int NULL DEFAULT NULL COMMENT '投入ステップ番号',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_bom_line_header`(`header_id` ASC) USING BTREE,
  INDEX `idx_bom_line_parent_line`(`parent_line_id` ASC) USING BTREE,
  INDEX `idx_bom_line_component`(`component_product_cd` ASC) USING BTREE,
  CONSTRAINT `fk_bom_line_header` FOREIGN KEY (`header_id`) REFERENCES `product_bom_headers` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_bom_line_parent` FOREIGN KEY (`parent_line_id`) REFERENCES `product_bom_lines` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 193 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin COMMENT = '明細BOM行' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of product_bom_lines
-- ----------------------------
INSERT INTO `product_bom_lines` VALUES (1, 1, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 13:26:06', '2026-04-09 13:26:06');
INSERT INTO `product_bom_lines` VALUES (8, 3, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:08:06', '2026-04-09 14:08:06');
INSERT INTO `product_bom_lines` VALUES (9, 4, NULL, 10, 'material', NULL, '10018', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:08:14', '2026-04-09 14:08:14');
INSERT INTO `product_bom_lines` VALUES (10, 5, NULL, 10, 'material', NULL, '10018', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:11:23', '2026-04-09 14:11:23');
INSERT INTO `product_bom_lines` VALUES (11, 6, NULL, 10, 'material', NULL, '10018', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:11:34', '2026-04-09 14:11:34');
INSERT INTO `product_bom_lines` VALUES (12, 7, NULL, 10, 'material', NULL, '10020', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:12:04', '2026-04-09 14:12:04');
INSERT INTO `product_bom_lines` VALUES (13, 8, NULL, 10, 'material', NULL, '10019', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:12:37', '2026-04-09 14:12:37');
INSERT INTO `product_bom_lines` VALUES (14, 9, NULL, 10, 'material', NULL, '10020', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:12:46', '2026-04-09 14:12:46');
INSERT INTO `product_bom_lines` VALUES (16, 11, NULL, 10, 'material', NULL, '10016', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:13:17', '2026-04-09 14:13:17');
INSERT INTO `product_bom_lines` VALUES (17, 12, NULL, 10, 'material', NULL, '10020', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:16:35', '2026-04-09 14:16:35');
INSERT INTO `product_bom_lines` VALUES (19, 13, NULL, 10, 'material', NULL, '10018', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:17:22', '2026-04-09 14:17:22');
INSERT INTO `product_bom_lines` VALUES (20, 13, NULL, 20, 'subassy', 'K0003', NULL, 1.000000, '個', 0.00, 'KT07', 4, NULL, '2026-04-09 14:17:22', '2026-04-09 14:17:22');
INSERT INTO `product_bom_lines` VALUES (21, 14, NULL, 10, 'material', NULL, '10030', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:30:25', '2026-04-09 14:30:25');
INSERT INTO `product_bom_lines` VALUES (22, 15, NULL, 10, 'material', NULL, '10030', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:30:34', '2026-04-09 14:30:34');
INSERT INTO `product_bom_lines` VALUES (23, 16, NULL, 10, 'material', NULL, '10023', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:31:07', '2026-04-09 14:31:07');
INSERT INTO `product_bom_lines` VALUES (24, 16, NULL, 20, 'subassy', 'K0019', NULL, 1.000000, '本', 0.00, 'KT07', 5, NULL, '2026-04-09 14:31:07', '2026-04-09 14:31:07');
INSERT INTO `product_bom_lines` VALUES (25, 16, NULL, 30, 'subassy', 'K0065', NULL, 1.000000, '個', 0.00, 'KT07', 5, NULL, '2026-04-09 14:31:07', '2026-04-09 14:31:07');
INSERT INTO `product_bom_lines` VALUES (26, 17, NULL, 10, 'material', NULL, '10023', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:31:36', '2026-04-09 14:31:36');
INSERT INTO `product_bom_lines` VALUES (27, 17, NULL, 20, 'subassy', 'K0019', NULL, 1.000000, '本', 0.00, 'KT07', 5, NULL, '2026-04-09 14:31:36', '2026-04-09 14:31:36');
INSERT INTO `product_bom_lines` VALUES (28, 17, NULL, 30, 'subassy', 'K0065', NULL, 1.000000, '個', 0.00, 'KT07', 5, NULL, '2026-04-09 14:31:36', '2026-04-09 14:31:36');
INSERT INTO `product_bom_lines` VALUES (29, 18, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:32:07', '2026-04-09 14:32:07');
INSERT INTO `product_bom_lines` VALUES (30, 18, NULL, 20, 'subassy', 'K0052', NULL, 1.000000, '個', 0.00, 'KT07', 7, NULL, '2026-04-09 14:32:07', '2026-04-09 14:32:07');
INSERT INTO `product_bom_lines` VALUES (31, 19, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:32:27', '2026-04-09 14:32:27');
INSERT INTO `product_bom_lines` VALUES (32, 20, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:32:34', '2026-04-09 14:32:34');
INSERT INTO `product_bom_lines` VALUES (33, 21, NULL, 10, 'material', NULL, '10023', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:32:41', '2026-04-09 14:32:41');
INSERT INTO `product_bom_lines` VALUES (34, 22, NULL, 10, 'material', NULL, '10018', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:32:48', '2026-04-09 14:32:48');
INSERT INTO `product_bom_lines` VALUES (35, 23, NULL, 10, 'material', NULL, '10124', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:32:57', '2026-04-09 14:32:57');
INSERT INTO `product_bom_lines` VALUES (36, 24, NULL, 10, 'material', NULL, '10084', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:33:04', '2026-04-09 14:33:04');
INSERT INTO `product_bom_lines` VALUES (37, 25, NULL, 10, 'subassy', 'K0042', NULL, 1.000000, '個', 0.00, 'KT01', 1, NULL, '2026-04-09 14:33:42', '2026-04-09 14:33:42');
INSERT INTO `product_bom_lines` VALUES (38, 25, NULL, 20, 'subassy', 'K0072', NULL, 1.000000, '個', 0.00, 'KT07', 6, NULL, '2026-04-09 14:33:42', '2026-04-09 14:33:42');
INSERT INTO `product_bom_lines` VALUES (39, 26, NULL, 10, 'material', NULL, '10002', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:34:10', '2026-04-09 14:34:10');
INSERT INTO `product_bom_lines` VALUES (40, 27, NULL, 10, 'material', NULL, '10002', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:34:18', '2026-04-09 14:34:18');
INSERT INTO `product_bom_lines` VALUES (41, 28, NULL, 10, 'material', NULL, '10002', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:34:24', '2026-04-09 14:34:24');
INSERT INTO `product_bom_lines` VALUES (42, 29, NULL, 10, 'material', NULL, '10002', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:34:30', '2026-04-09 14:34:30');
INSERT INTO `product_bom_lines` VALUES (43, 30, NULL, 10, 'material', NULL, '10002', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:34:37', '2026-04-09 14:34:37');
INSERT INTO `product_bom_lines` VALUES (44, 31, NULL, 10, 'subassy', 'K0096', NULL, 1.000000, '個', 0.00, 'KT01', 1, NULL, '2026-04-09 14:38:04', '2026-04-09 14:38:04');
INSERT INTO `product_bom_lines` VALUES (45, 31, NULL, 20, 'subassy', 'K0097', NULL, 1.000000, '個', 0.00, 'KT09', 4, NULL, '2026-04-09 14:38:04', '2026-04-09 14:38:04');
INSERT INTO `product_bom_lines` VALUES (46, 31, NULL, 30, 'subassy', 'K0101', NULL, 3.000000, '個', 0.00, 'KT09', 4, NULL, '2026-04-09 14:38:04', '2026-04-09 14:38:04');
INSERT INTO `product_bom_lines` VALUES (47, 32, NULL, 10, 'material', NULL, '10010', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:38:39', '2026-04-09 14:38:39');
INSERT INTO `product_bom_lines` VALUES (48, 33, NULL, 10, 'material', NULL, '10091', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:38:48', '2026-04-09 14:38:48');
INSERT INTO `product_bom_lines` VALUES (49, 34, NULL, 10, 'material', NULL, '10124', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:40:24', '2026-04-09 14:40:24');
INSERT INTO `product_bom_lines` VALUES (50, 34, NULL, 20, 'subassy', 'K0035', NULL, 1.000000, '個', 0.00, 'KT07', 5, NULL, '2026-04-09 14:40:24', '2026-04-09 14:40:24');
INSERT INTO `product_bom_lines` VALUES (51, 34, NULL, 30, 'subassy', 'K0036', NULL, 1.000000, '個', 0.00, 'KT07', 5, NULL, '2026-04-09 14:40:24', '2026-04-09 14:40:24');
INSERT INTO `product_bom_lines` VALUES (52, 35, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:40:38', '2026-04-09 14:40:38');
INSERT INTO `product_bom_lines` VALUES (53, 36, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:40:44', '2026-04-09 14:40:44');
INSERT INTO `product_bom_lines` VALUES (54, 37, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:40:51', '2026-04-09 14:40:51');
INSERT INTO `product_bom_lines` VALUES (55, 38, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:40:59', '2026-04-09 14:40:59');
INSERT INTO `product_bom_lines` VALUES (56, 39, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:41:13', '2026-04-09 14:41:13');
INSERT INTO `product_bom_lines` VALUES (57, 40, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:41:30', '2026-04-09 14:41:30');
INSERT INTO `product_bom_lines` VALUES (58, 40, NULL, 20, 'subassy', 'K0070', NULL, 1.000000, '個', 0.00, 'KT07', 7, NULL, '2026-04-09 14:41:30', '2026-04-09 14:41:30');
INSERT INTO `product_bom_lines` VALUES (59, 41, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:41:49', '2026-04-09 14:41:49');
INSERT INTO `product_bom_lines` VALUES (60, 41, NULL, 20, 'subassy', 'K0070', NULL, 1.000000, '個', 0.00, 'KT07', 7, NULL, '2026-04-09 14:41:49', '2026-04-09 14:41:49');
INSERT INTO `product_bom_lines` VALUES (61, 42, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:42:02', '2026-04-09 14:42:02');
INSERT INTO `product_bom_lines` VALUES (62, 42, NULL, 20, 'subassy', 'K0070', NULL, 1.000000, '個', 0.00, 'KT07', 7, NULL, '2026-04-09 14:42:02', '2026-04-09 14:42:02');
INSERT INTO `product_bom_lines` VALUES (63, 43, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:42:14', '2026-04-09 14:42:14');
INSERT INTO `product_bom_lines` VALUES (64, 43, NULL, 20, 'subassy', 'K0070', NULL, 1.000000, '個', 0.00, 'KT07', 7, NULL, '2026-04-09 14:42:14', '2026-04-09 14:42:14');
INSERT INTO `product_bom_lines` VALUES (65, 44, NULL, 10, 'material', NULL, '10079', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:42:21', '2026-04-09 14:42:21');
INSERT INTO `product_bom_lines` VALUES (66, 45, NULL, 10, 'material', NULL, '10034', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:42:33', '2026-04-09 14:42:33');
INSERT INTO `product_bom_lines` VALUES (67, 46, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:42:42', '2026-04-09 14:42:42');
INSERT INTO `product_bom_lines` VALUES (68, 47, NULL, 10, 'material', NULL, '10054', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:42:54', '2026-04-09 14:42:54');
INSERT INTO `product_bom_lines` VALUES (69, 48, NULL, 10, 'material', NULL, '10063', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:43:53', '2026-04-09 14:43:53');
INSERT INTO `product_bom_lines` VALUES (71, 50, NULL, 10, 'material', NULL, '10063', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:44:07', '2026-04-09 14:44:07');
INSERT INTO `product_bom_lines` VALUES (72, 51, NULL, 10, 'material', NULL, '10127', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:44:25', '2026-04-09 14:44:25');
INSERT INTO `product_bom_lines` VALUES (73, 52, NULL, 10, 'material', NULL, '10061', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:44:31', '2026-04-09 14:44:31');
INSERT INTO `product_bom_lines` VALUES (74, 53, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:44:44', '2026-04-09 14:44:44');
INSERT INTO `product_bom_lines` VALUES (75, 54, NULL, 10, 'material', NULL, '10015', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:44:50', '2026-04-09 14:44:50');
INSERT INTO `product_bom_lines` VALUES (76, 55, NULL, 10, 'material', NULL, '10015', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:45:01', '2026-04-09 14:45:01');
INSERT INTO `product_bom_lines` VALUES (77, 56, NULL, 10, 'material', NULL, '10123', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:45:08', '2026-04-09 14:45:08');
INSERT INTO `product_bom_lines` VALUES (78, 57, NULL, 10, 'material', NULL, '10018', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:45:15', '2026-04-09 14:45:15');
INSERT INTO `product_bom_lines` VALUES (79, 58, NULL, 10, 'material', NULL, '10040', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:45:22', '2026-04-09 14:45:22');
INSERT INTO `product_bom_lines` VALUES (80, 59, NULL, 10, 'material', NULL, '10023', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:45:30', '2026-04-09 14:45:30');
INSERT INTO `product_bom_lines` VALUES (81, 60, NULL, 10, 'material', NULL, '10126', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:45:40', '2026-04-09 14:45:40');
INSERT INTO `product_bom_lines` VALUES (82, 61, NULL, 10, 'material', NULL, '10123', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:46:11', '2026-04-09 14:46:11');
INSERT INTO `product_bom_lines` VALUES (83, 61, NULL, 20, 'subassy', 'K0078', NULL, 1.000000, '個', 0.00, 'KT07', 3, NULL, '2026-04-09 14:46:11', '2026-04-09 14:46:11');
INSERT INTO `product_bom_lines` VALUES (84, 62, NULL, 10, 'material', NULL, '10040', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:52:23', '2026-04-09 14:52:23');
INSERT INTO `product_bom_lines` VALUES (85, 63, NULL, 10, 'material', NULL, '10040', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:52:29', '2026-04-09 14:52:29');
INSERT INTO `product_bom_lines` VALUES (86, 64, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:52:36', '2026-04-09 14:52:36');
INSERT INTO `product_bom_lines` VALUES (87, 65, NULL, 10, 'material', NULL, '10010', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:52:59', '2026-04-09 14:52:59');
INSERT INTO `product_bom_lines` VALUES (88, 65, NULL, 20, 'subassy', 'K0080', NULL, 1.000000, '個', 0.00, 'KT07', 5, NULL, '2026-04-09 14:52:59', '2026-04-09 14:52:59');
INSERT INTO `product_bom_lines` VALUES (89, 65, NULL, 30, 'subassy', 'K0081', NULL, 1.000000, '個', 0.00, 'KT07', 5, NULL, '2026-04-09 14:52:59', '2026-04-09 14:52:59');
INSERT INTO `product_bom_lines` VALUES (90, 66, NULL, 10, 'material', NULL, '10034', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:54:47', '2026-04-09 14:54:47');
INSERT INTO `product_bom_lines` VALUES (91, 67, NULL, 10, 'material', NULL, '10064', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:54:58', '2026-04-09 14:54:58');
INSERT INTO `product_bom_lines` VALUES (92, 68, NULL, 10, 'material', NULL, '10065', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:55:04', '2026-04-09 14:55:04');
INSERT INTO `product_bom_lines` VALUES (93, 69, NULL, 10, 'material', NULL, '10121', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:55:24', '2026-04-09 14:55:24');
INSERT INTO `product_bom_lines` VALUES (94, 69, NULL, 20, 'subassy', 'K0079', NULL, 1.000000, '個', 0.00, 'KT07', 4, NULL, '2026-04-09 14:55:24', '2026-04-09 14:55:24');
INSERT INTO `product_bom_lines` VALUES (95, 70, NULL, 10, 'material', NULL, '10122', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:55:35', '2026-04-09 14:55:35');
INSERT INTO `product_bom_lines` VALUES (96, 71, NULL, 10, 'material', NULL, '10066', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:55:41', '2026-04-09 14:55:41');
INSERT INTO `product_bom_lines` VALUES (97, 72, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:55:47', '2026-04-09 14:55:47');
INSERT INTO `product_bom_lines` VALUES (98, 73, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:55:53', '2026-04-09 14:55:53');
INSERT INTO `product_bom_lines` VALUES (99, 74, NULL, 10, 'material', NULL, '10080', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:56:21', '2026-04-09 14:56:21');
INSERT INTO `product_bom_lines` VALUES (100, 74, NULL, 20, 'subassy', 'K0099', NULL, 1.000000, '個', 0.00, 'KT07', 5, NULL, '2026-04-09 14:56:21', '2026-04-09 14:56:21');
INSERT INTO `product_bom_lines` VALUES (101, 75, NULL, 10, 'material', NULL, '10069', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:56:32', '2026-04-09 14:56:32');
INSERT INTO `product_bom_lines` VALUES (102, 76, NULL, 10, 'material', NULL, '10069', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:56:38', '2026-04-09 14:56:38');
INSERT INTO `product_bom_lines` VALUES (103, 77, NULL, 10, 'material', NULL, '10123', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:56:45', '2026-04-09 14:56:45');
INSERT INTO `product_bom_lines` VALUES (104, 78, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:56:51', '2026-04-09 14:56:51');
INSERT INTO `product_bom_lines` VALUES (105, 79, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:56:58', '2026-04-09 14:56:58');
INSERT INTO `product_bom_lines` VALUES (106, 80, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:57:17', '2026-04-09 14:57:17');
INSERT INTO `product_bom_lines` VALUES (107, 80, NULL, 20, 'subassy', 'K0086', NULL, 1.000000, '個', 0.00, 'KT07', 3, NULL, '2026-04-09 14:57:17', '2026-04-09 14:57:17');
INSERT INTO `product_bom_lines` VALUES (108, 81, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:57:31', '2026-04-09 14:57:31');
INSERT INTO `product_bom_lines` VALUES (109, 82, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:57:37', '2026-04-09 14:57:37');
INSERT INTO `product_bom_lines` VALUES (110, 83, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:57:43', '2026-04-09 14:57:43');
INSERT INTO `product_bom_lines` VALUES (111, 84, NULL, 10, 'material', NULL, '10023', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:57:50', '2026-04-09 14:57:50');
INSERT INTO `product_bom_lines` VALUES (112, 85, NULL, 10, 'material', NULL, '10073', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:58:17', '2026-04-09 14:58:17');
INSERT INTO `product_bom_lines` VALUES (113, 85, NULL, 20, 'subassy', 'K0098', NULL, 1.000000, '個', 0.00, 'KT07', 6, NULL, '2026-04-09 14:58:17', '2026-04-09 14:58:17');
INSERT INTO `product_bom_lines` VALUES (114, 86, NULL, 10, 'material', NULL, '10073', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:58:39', '2026-04-09 14:58:39');
INSERT INTO `product_bom_lines` VALUES (115, 87, NULL, 10, 'material', NULL, '10073', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:59:03', '2026-04-09 14:59:03');
INSERT INTO `product_bom_lines` VALUES (116, 87, NULL, 20, 'subassy', 'K0091', NULL, 1.000000, '個', 0.00, 'KT07', 6, NULL, '2026-04-09 14:59:03', '2026-04-09 14:59:03');
INSERT INTO `product_bom_lines` VALUES (117, 88, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:59:37', '2026-04-09 14:59:37');
INSERT INTO `product_bom_lines` VALUES (118, 88, NULL, 20, 'subassy', 'K0070', NULL, 1.000000, '個', 0.00, 'KT07', 7, NULL, '2026-04-09 14:59:37', '2026-04-09 14:59:37');
INSERT INTO `product_bom_lines` VALUES (119, 89, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:59:46', '2026-04-09 14:59:46');
INSERT INTO `product_bom_lines` VALUES (120, 90, NULL, 10, 'material', NULL, '10018', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 14:59:53', '2026-04-09 14:59:53');
INSERT INTO `product_bom_lines` VALUES (121, 91, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:00:00', '2026-04-09 15:00:00');
INSERT INTO `product_bom_lines` VALUES (122, 92, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:01:39', '2026-04-09 15:01:39');
INSERT INTO `product_bom_lines` VALUES (123, 92, NULL, 20, 'subassy', 'K0093', NULL, 1.000000, '個', 0.00, 'KT07', 4, NULL, '2026-04-09 15:01:39', '2026-04-09 15:01:39');
INSERT INTO `product_bom_lines` VALUES (124, 93, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:02:01', '2026-04-09 15:02:01');
INSERT INTO `product_bom_lines` VALUES (125, 94, NULL, 10, 'material', NULL, '10030', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:02:12', '2026-04-09 15:02:12');
INSERT INTO `product_bom_lines` VALUES (126, 95, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:02:25', '2026-04-09 15:02:25');
INSERT INTO `product_bom_lines` VALUES (127, 96, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:02:50', '2026-04-09 15:02:50');
INSERT INTO `product_bom_lines` VALUES (128, 96, NULL, 20, 'subassy', 'K0095', NULL, 1.000000, '個', 0.00, 'KT07', 4, NULL, '2026-04-09 15:02:50', '2026-04-09 15:02:50');
INSERT INTO `product_bom_lines` VALUES (129, 97, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:07:07', '2026-04-09 15:07:07');
INSERT INTO `product_bom_lines` VALUES (130, 98, NULL, 10, 'material', NULL, '10080', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:07:23', '2026-04-09 15:07:23');
INSERT INTO `product_bom_lines` VALUES (131, 98, NULL, 20, 'subassy', 'K0094', NULL, 1.000000, '個', 0.00, 'KT07', 5, NULL, '2026-04-09 15:07:23', '2026-04-09 15:07:23');
INSERT INTO `product_bom_lines` VALUES (132, 99, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:07:29', '2026-04-09 15:07:29');
INSERT INTO `product_bom_lines` VALUES (133, 100, NULL, 10, 'material', NULL, '10123', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:07:36', '2026-04-09 15:07:36');
INSERT INTO `product_bom_lines` VALUES (134, 101, NULL, 10, 'material', NULL, '10028', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:07:45', '2026-04-09 15:07:45');
INSERT INTO `product_bom_lines` VALUES (135, 102, NULL, 10, 'material', NULL, '10063', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:07:51', '2026-04-09 15:07:51');
INSERT INTO `product_bom_lines` VALUES (136, 103, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:07:57', '2026-04-09 15:07:57');
INSERT INTO `product_bom_lines` VALUES (137, 104, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:08:03', '2026-04-09 15:08:03');
INSERT INTO `product_bom_lines` VALUES (138, 105, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:08:09', '2026-04-09 15:08:09');
INSERT INTO `product_bom_lines` VALUES (139, 106, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:08:16', '2026-04-09 15:08:16');
INSERT INTO `product_bom_lines` VALUES (140, 107, NULL, 10, 'material', NULL, '10073', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:08:24', '2026-04-09 15:08:24');
INSERT INTO `product_bom_lines` VALUES (141, 108, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:08:40', '2026-04-09 15:08:40');
INSERT INTO `product_bom_lines` VALUES (142, 108, NULL, 20, 'subassy', 'K0102', NULL, 1.000000, '個', 0.00, 'KT07', 4, NULL, '2026-04-09 15:08:40', '2026-04-09 15:08:40');
INSERT INTO `product_bom_lines` VALUES (143, 109, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:08:58', '2026-04-09 15:08:58');
INSERT INTO `product_bom_lines` VALUES (144, 109, NULL, 20, 'subassy', 'K0102', NULL, 1.000000, '個', 0.00, 'KT07', 4, NULL, '2026-04-09 15:08:58', '2026-04-09 15:08:58');
INSERT INTO `product_bom_lines` VALUES (145, 110, NULL, 10, 'material', NULL, '10076', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:09:05', '2026-04-09 15:09:05');
INSERT INTO `product_bom_lines` VALUES (146, 111, NULL, 10, 'material', NULL, '10087', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:09:11', '2026-04-09 15:09:11');
INSERT INTO `product_bom_lines` VALUES (147, 112, NULL, 10, 'material', NULL, '10087', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:09:17', '2026-04-09 15:09:17');
INSERT INTO `product_bom_lines` VALUES (150, 115, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:09:39', '2026-04-09 15:09:39');
INSERT INTO `product_bom_lines` VALUES (151, 116, NULL, 10, 'material', NULL, '10101', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:09:46', '2026-04-09 15:09:46');
INSERT INTO `product_bom_lines` VALUES (152, 117, NULL, 10, 'material', NULL, '10101', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:09:52', '2026-04-09 15:09:52');
INSERT INTO `product_bom_lines` VALUES (153, 118, NULL, 10, 'material', NULL, '10010', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:10:03', '2026-04-09 15:10:03');
INSERT INTO `product_bom_lines` VALUES (154, 119, NULL, 10, 'material', NULL, '10010', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:10:10', '2026-04-09 15:10:10');
INSERT INTO `product_bom_lines` VALUES (155, 120, NULL, 10, 'material', NULL, '10010', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:10:18', '2026-04-09 15:10:18');
INSERT INTO `product_bom_lines` VALUES (156, 121, NULL, 10, 'material', NULL, '10063', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:10:28', '2026-04-09 15:10:28');
INSERT INTO `product_bom_lines` VALUES (157, 122, NULL, 10, 'material', NULL, '10030', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:10:40', '2026-04-09 15:10:40');
INSERT INTO `product_bom_lines` VALUES (158, 123, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:35:12', '2026-04-09 15:35:12');
INSERT INTO `product_bom_lines` VALUES (159, 124, NULL, 10, 'material', NULL, '10055', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:35:17', '2026-04-09 15:35:17');
INSERT INTO `product_bom_lines` VALUES (160, 125, NULL, 10, 'material', NULL, '10069', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:37:21', '2026-04-09 15:37:21');
INSERT INTO `product_bom_lines` VALUES (161, 126, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:37:46', '2026-04-09 15:37:46');
INSERT INTO `product_bom_lines` VALUES (162, 127, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:37:55', '2026-04-09 15:37:55');
INSERT INTO `product_bom_lines` VALUES (163, 128, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:38:03', '2026-04-09 15:38:03');
INSERT INTO `product_bom_lines` VALUES (164, 129, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:38:14', '2026-04-09 15:38:14');
INSERT INTO `product_bom_lines` VALUES (165, 130, NULL, 10, 'material', NULL, '10124', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:38:23', '2026-04-09 15:38:23');
INSERT INTO `product_bom_lines` VALUES (166, 131, NULL, 10, 'material', NULL, '10123', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:38:31', '2026-04-09 15:38:31');
INSERT INTO `product_bom_lines` VALUES (167, 132, NULL, 10, 'material', NULL, '10111', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:38:38', '2026-04-09 15:38:38');
INSERT INTO `product_bom_lines` VALUES (168, 133, NULL, 10, 'material', NULL, '10063', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:38:47', '2026-04-09 15:38:47');
INSERT INTO `product_bom_lines` VALUES (169, 134, NULL, 10, 'material', NULL, '10034', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 15:38:57', '2026-04-09 15:38:57');
INSERT INTO `product_bom_lines` VALUES (170, 135, NULL, 10, 'material', NULL, '10123', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:07:07', '2026-04-09 16:07:07');
INSERT INTO `product_bom_lines` VALUES (171, 135, NULL, 20, 'subassy', 'K0105', NULL, 1.000000, '個', 0.00, 'KT07', 6, NULL, '2026-04-09 16:07:07', '2026-04-09 16:07:07');
INSERT INTO `product_bom_lines` VALUES (172, 135, NULL, 30, 'subassy', 'K0106', NULL, 1.000000, '個', 0.00, 'KT07', 6, NULL, '2026-04-09 16:07:07', '2026-04-09 16:07:07');
INSERT INTO `product_bom_lines` VALUES (173, 136, NULL, 10, 'material', NULL, '10010', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:07:20', '2026-04-09 16:07:20');
INSERT INTO `product_bom_lines` VALUES (174, 137, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:07:26', '2026-04-09 16:07:26');
INSERT INTO `product_bom_lines` VALUES (175, 138, NULL, 10, 'material', NULL, '10018', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:07:34', '2026-04-09 16:07:34');
INSERT INTO `product_bom_lines` VALUES (176, 139, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:08:17', '2026-04-09 16:08:17');
INSERT INTO `product_bom_lines` VALUES (177, 139, NULL, 20, 'subassy', 'K0077', NULL, 1.000000, '個', 0.00, 'KT07', 7, NULL, '2026-04-09 16:08:17', '2026-04-09 16:08:17');
INSERT INTO `product_bom_lines` VALUES (178, 140, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:08:27', '2026-04-09 16:08:27');
INSERT INTO `product_bom_lines` VALUES (179, 141, NULL, 10, 'material', NULL, '10036', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:09:41', '2026-04-09 16:09:41');
INSERT INTO `product_bom_lines` VALUES (180, 142, NULL, 10, 'material', NULL, '10126', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:09:54', '2026-04-09 16:09:54');
INSERT INTO `product_bom_lines` VALUES (181, 142, NULL, 20, 'subassy', 'K0103', NULL, 1.000000, '個', 0.00, 'KT07', 3, NULL, '2026-04-09 16:09:54', '2026-04-09 16:09:54');
INSERT INTO `product_bom_lines` VALUES (182, 143, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:10:22', '2026-04-09 16:10:22');
INSERT INTO `product_bom_lines` VALUES (183, 143, NULL, 20, 'subassy', 'K0086', NULL, 1.000000, '個', 0.00, 'KT07', 4, NULL, '2026-04-09 16:10:22', '2026-04-09 16:10:22');
INSERT INTO `product_bom_lines` VALUES (184, 144, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:10:50', '2026-04-09 16:10:50');
INSERT INTO `product_bom_lines` VALUES (185, 144, NULL, 20, 'subassy', 'K0087', NULL, 1.000000, '個', 0.00, 'KT07', 6, NULL, '2026-04-09 16:10:50', '2026-04-09 16:10:50');
INSERT INTO `product_bom_lines` VALUES (186, 144, NULL, 30, 'subassy', 'K0088', NULL, 1.000000, '個', 0.00, 'KT07', 6, NULL, '2026-04-09 16:10:50', '2026-04-09 16:10:50');
INSERT INTO `product_bom_lines` VALUES (187, 145, NULL, 10, 'material', NULL, '10124', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:11:04', '2026-04-09 16:11:04');
INSERT INTO `product_bom_lines` VALUES (188, 146, NULL, 10, 'material', NULL, '10060', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:11:18', '2026-04-09 16:11:18');
INSERT INTO `product_bom_lines` VALUES (189, 147, NULL, 10, 'material', NULL, '10084', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:11:34', '2026-04-09 16:11:34');
INSERT INTO `product_bom_lines` VALUES (190, 148, NULL, 10, 'material', NULL, '10030', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:11:48', '2026-04-09 16:11:48');
INSERT INTO `product_bom_lines` VALUES (191, 149, NULL, 10, 'material', NULL, '10031', 1.000000, '本', 0.00, 'KT01', 1, NULL, '2026-04-09 16:11:59', '2026-04-09 16:11:59');
INSERT INTO `product_bom_lines` VALUES (192, 150, NULL, 10, 'subassy', 'K0090', NULL, 1.000000, '個', 0.00, 'KT01', 1, NULL, '2026-04-20 14:31:41', '2026-04-20 14:31:41');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
