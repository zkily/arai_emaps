SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for product_bom_headers
-- ----------------------------
DROP TABLE IF EXISTS `product_bom_headers`;
CREATE TABLE `product_bom_headers`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `parent_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '親製品CD',
  `bom_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'production' COMMENT 'BOM種別 (engineering/production)',
  `revision` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '1' COMMENT '版番',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'active' COMMENT '状態 (active/historical)',
  `effective_from` date NULL DEFAULT NULL COMMENT '有効開始日',
  `effective_to` date NULL DEFAULT NULL COMMENT '有効終了日 (NULL=無期限)',
  `base_quantity` decimal(12, 4) NOT NULL DEFAULT 1.0000 COMMENT '基準数量',
  `uom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '個' COMMENT '単位',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_bom_hdr_parent`(`parent_product_cd` ASC) USING BTREE,
  INDEX `idx_bom_hdr_effective`(`parent_product_cd` ASC, `bom_type` ASC, `effective_from` ASC, `effective_to` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 151 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin COMMENT = '明細BOMヘッダ' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of product_bom_headers
-- ----------------------------
INSERT INTO `product_bom_headers` VALUES (1, '90011', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 13:26:06', '2026-04-09 13:26:06');
INSERT INTO `product_bom_headers` VALUES (3, '90012', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 13:40:42', '2026-04-09 14:08:06');
INSERT INTO `product_bom_headers` VALUES (4, '90141', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:07:09', '2026-04-09 14:08:14');
INSERT INTO `product_bom_headers` VALUES (5, '90142', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:07:17', '2026-04-09 14:11:23');
INSERT INTO `product_bom_headers` VALUES (6, '90191', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:07:24', '2026-04-09 14:11:34');
INSERT INTO `product_bom_headers` VALUES (7, '90271', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:07:36', '2026-04-09 14:12:04');
INSERT INTO `product_bom_headers` VALUES (8, '90281', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:12:37', '2026-04-09 14:12:37');
INSERT INTO `product_bom_headers` VALUES (9, '90291', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:12:46', '2026-04-09 14:12:46');
INSERT INTO `product_bom_headers` VALUES (11, '90301', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:13:17', '2026-04-09 14:13:17');
INSERT INTO `product_bom_headers` VALUES (12, '90311', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:16:35', '2026-04-09 14:16:35');
INSERT INTO `product_bom_headers` VALUES (13, '90351', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:17:03', '2026-04-09 14:17:03');
INSERT INTO `product_bom_headers` VALUES (14, '90631', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:30:25', '2026-04-09 14:30:25');
INSERT INTO `product_bom_headers` VALUES (15, '90633', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:30:34', '2026-04-09 14:30:34');
INSERT INTO `product_bom_headers` VALUES (16, '90661', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:31:07', '2026-04-09 14:31:07');
INSERT INTO `product_bom_headers` VALUES (17, '90681', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:31:36', '2026-04-09 14:31:36');
INSERT INTO `product_bom_headers` VALUES (18, '90711', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:32:07', '2026-04-09 14:32:07');
INSERT INTO `product_bom_headers` VALUES (19, '90741', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:32:27', '2026-04-09 14:32:27');
INSERT INTO `product_bom_headers` VALUES (20, '90743', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:32:34', '2026-04-09 14:32:34');
INSERT INTO `product_bom_headers` VALUES (21, '90771', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:32:41', '2026-04-09 14:32:41');
INSERT INTO `product_bom_headers` VALUES (22, '90841', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:32:48', '2026-04-09 14:32:48');
INSERT INTO `product_bom_headers` VALUES (23, '90932', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:32:57', '2026-04-09 14:32:57');
INSERT INTO `product_bom_headers` VALUES (24, '90961', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:33:04', '2026-04-09 14:33:04');
INSERT INTO `product_bom_headers` VALUES (25, '90991', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:33:42', '2026-04-09 14:33:42');
INSERT INTO `product_bom_headers` VALUES (26, '91001', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:34:10', '2026-04-09 14:34:10');
INSERT INTO `product_bom_headers` VALUES (27, '91002', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:34:18', '2026-04-09 14:34:18');
INSERT INTO `product_bom_headers` VALUES (28, '91011', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:34:24', '2026-04-09 14:34:24');
INSERT INTO `product_bom_headers` VALUES (29, '91012', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:34:30', '2026-04-09 14:34:30');
INSERT INTO `product_bom_headers` VALUES (30, '91013', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:34:37', '2026-04-09 14:34:37');
INSERT INTO `product_bom_headers` VALUES (31, '91021', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:38:04', '2026-04-09 14:38:04');
INSERT INTO `product_bom_headers` VALUES (32, '91111', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:38:39', '2026-04-09 14:38:39');
INSERT INTO `product_bom_headers` VALUES (33, '91151', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:38:48', '2026-04-09 14:38:48');
INSERT INTO `product_bom_headers` VALUES (34, '91181', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:40:24', '2026-04-09 14:40:24');
INSERT INTO `product_bom_headers` VALUES (35, '91251', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:40:38', '2026-04-09 14:40:38');
INSERT INTO `product_bom_headers` VALUES (36, '91253', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:40:44', '2026-04-09 14:40:44');
INSERT INTO `product_bom_headers` VALUES (37, '91254', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:40:51', '2026-04-09 14:40:51');
INSERT INTO `product_bom_headers` VALUES (38, '91261', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:40:59', '2026-04-09 14:40:59');
INSERT INTO `product_bom_headers` VALUES (39, '91271', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:41:13', '2026-04-09 14:41:13');
INSERT INTO `product_bom_headers` VALUES (40, '91301', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:41:30', '2026-04-09 14:41:30');
INSERT INTO `product_bom_headers` VALUES (41, '91302', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:41:49', '2026-04-09 14:41:49');
INSERT INTO `product_bom_headers` VALUES (42, '91303', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:42:02', '2026-04-09 14:42:02');
INSERT INTO `product_bom_headers` VALUES (43, '91304', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:42:14', '2026-04-09 14:42:14');
INSERT INTO `product_bom_headers` VALUES (44, '91321', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:42:21', '2026-04-09 14:42:21');
INSERT INTO `product_bom_headers` VALUES (45, '91331', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:42:33', '2026-04-09 14:42:33');
INSERT INTO `product_bom_headers` VALUES (46, '91401', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:42:42', '2026-04-09 14:42:42');
INSERT INTO `product_bom_headers` VALUES (47, '91411', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:42:54', '2026-04-09 14:42:54');
INSERT INTO `product_bom_headers` VALUES (48, '91441', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:43:53', '2026-04-09 14:43:53');
INSERT INTO `product_bom_headers` VALUES (50, '91442', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:44:07', '2026-04-09 14:44:07');
INSERT INTO `product_bom_headers` VALUES (51, '91443', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:44:25', '2026-04-09 14:44:25');
INSERT INTO `product_bom_headers` VALUES (52, '91451', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:44:31', '2026-04-09 14:44:31');
INSERT INTO `product_bom_headers` VALUES (53, '91461', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:44:44', '2026-04-09 14:44:44');
INSERT INTO `product_bom_headers` VALUES (54, '91471', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:44:50', '2026-04-09 14:44:50');
INSERT INTO `product_bom_headers` VALUES (55, '91481', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:45:01', '2026-04-09 14:45:01');
INSERT INTO `product_bom_headers` VALUES (56, '91491', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:45:08', '2026-04-09 14:45:08');
INSERT INTO `product_bom_headers` VALUES (57, '91521', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:45:15', '2026-04-09 14:45:15');
INSERT INTO `product_bom_headers` VALUES (58, '91581', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:45:22', '2026-04-09 14:45:22');
INSERT INTO `product_bom_headers` VALUES (59, '91591', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:45:30', '2026-04-09 14:45:30');
INSERT INTO `product_bom_headers` VALUES (60, '91621', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:45:40', '2026-04-09 14:45:40');
INSERT INTO `product_bom_headers` VALUES (61, '91631', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:46:11', '2026-04-09 14:46:11');
INSERT INTO `product_bom_headers` VALUES (62, '91671', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:52:23', '2026-04-09 14:52:23');
INSERT INTO `product_bom_headers` VALUES (63, '91681', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:52:29', '2026-04-09 14:52:29');
INSERT INTO `product_bom_headers` VALUES (64, '91711', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:52:36', '2026-04-09 14:52:36');
INSERT INTO `product_bom_headers` VALUES (65, '91741', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:52:59', '2026-04-09 14:52:59');
INSERT INTO `product_bom_headers` VALUES (66, '91751', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:54:47', '2026-04-09 14:54:47');
INSERT INTO `product_bom_headers` VALUES (67, '91771', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:54:58', '2026-04-09 14:54:58');
INSERT INTO `product_bom_headers` VALUES (68, '91781', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:55:04', '2026-04-09 14:55:04');
INSERT INTO `product_bom_headers` VALUES (69, '91791', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:55:24', '2026-04-09 14:55:24');
INSERT INTO `product_bom_headers` VALUES (70, '91811', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:55:35', '2026-04-09 14:55:35');
INSERT INTO `product_bom_headers` VALUES (71, '91831', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:55:41', '2026-04-09 14:55:41');
INSERT INTO `product_bom_headers` VALUES (72, '91841', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:55:47', '2026-04-09 14:55:47');
INSERT INTO `product_bom_headers` VALUES (73, '91851', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:55:53', '2026-04-09 14:55:53');
INSERT INTO `product_bom_headers` VALUES (74, '91861', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:56:21', '2026-04-09 14:56:21');
INSERT INTO `product_bom_headers` VALUES (75, '91881', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:56:32', '2026-04-09 14:56:32');
INSERT INTO `product_bom_headers` VALUES (76, '91882', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:56:38', '2026-04-09 14:56:38');
INSERT INTO `product_bom_headers` VALUES (77, '91891', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:56:45', '2026-04-09 14:56:45');
INSERT INTO `product_bom_headers` VALUES (78, '91901', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:56:51', '2026-04-09 14:56:51');
INSERT INTO `product_bom_headers` VALUES (79, '91911', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:56:58', '2026-04-09 14:56:58');
INSERT INTO `product_bom_headers` VALUES (80, '91931', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:57:17', '2026-04-09 14:57:17');
INSERT INTO `product_bom_headers` VALUES (81, '91951', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:57:31', '2026-04-09 14:57:31');
INSERT INTO `product_bom_headers` VALUES (82, '91952', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:57:37', '2026-04-09 14:57:37');
INSERT INTO `product_bom_headers` VALUES (83, '91953', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:57:43', '2026-04-09 14:57:43');
INSERT INTO `product_bom_headers` VALUES (84, '92001', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:57:50', '2026-04-09 14:57:50');
INSERT INTO `product_bom_headers` VALUES (85, '92011', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:58:17', '2026-04-09 14:58:17');
INSERT INTO `product_bom_headers` VALUES (86, '92021', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:58:39', '2026-04-09 14:58:39');
INSERT INTO `product_bom_headers` VALUES (87, '92031', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:59:03', '2026-04-09 14:59:03');
INSERT INTO `product_bom_headers` VALUES (88, '92041', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:59:37', '2026-04-09 14:59:37');
INSERT INTO `product_bom_headers` VALUES (89, '92051', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:59:46', '2026-04-09 14:59:46');
INSERT INTO `product_bom_headers` VALUES (90, '92071', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 14:59:53', '2026-04-09 14:59:53');
INSERT INTO `product_bom_headers` VALUES (91, '92091', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:00:00', '2026-04-09 15:00:00');
INSERT INTO `product_bom_headers` VALUES (92, '92101', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:01:39', '2026-04-09 15:01:39');
INSERT INTO `product_bom_headers` VALUES (93, '92131', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:02:01', '2026-04-09 15:02:01');
INSERT INTO `product_bom_headers` VALUES (94, '92111', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:02:12', '2026-04-09 15:02:12');
INSERT INTO `product_bom_headers` VALUES (95, '92121', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:02:25', '2026-04-09 15:02:25');
INSERT INTO `product_bom_headers` VALUES (96, '92141', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:02:50', '2026-04-09 15:02:50');
INSERT INTO `product_bom_headers` VALUES (97, '92151', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:07:07', '2026-04-09 15:07:07');
INSERT INTO `product_bom_headers` VALUES (98, '92161', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:07:23', '2026-04-09 15:07:23');
INSERT INTO `product_bom_headers` VALUES (99, '92181', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:07:29', '2026-04-09 15:07:29');
INSERT INTO `product_bom_headers` VALUES (100, '92191', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:07:36', '2026-04-09 15:07:36');
INSERT INTO `product_bom_headers` VALUES (101, '92201', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:07:45', '2026-04-09 15:07:45');
INSERT INTO `product_bom_headers` VALUES (102, '92211', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:07:51', '2026-04-09 15:07:51');
INSERT INTO `product_bom_headers` VALUES (103, '92221', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:07:57', '2026-04-09 15:07:57');
INSERT INTO `product_bom_headers` VALUES (104, '92222', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:08:03', '2026-04-09 15:08:03');
INSERT INTO `product_bom_headers` VALUES (105, '92231', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:08:09', '2026-04-09 15:08:09');
INSERT INTO `product_bom_headers` VALUES (106, '92241', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:08:16', '2026-04-09 15:08:16');
INSERT INTO `product_bom_headers` VALUES (107, '92281', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:08:24', '2026-04-09 15:08:24');
INSERT INTO `product_bom_headers` VALUES (108, '92291', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:08:40', '2026-04-09 15:08:40');
INSERT INTO `product_bom_headers` VALUES (109, '92292', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:08:58', '2026-04-09 15:08:58');
INSERT INTO `product_bom_headers` VALUES (110, '92301', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:09:05', '2026-04-09 15:09:05');
INSERT INTO `product_bom_headers` VALUES (111, '92321', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:09:11', '2026-04-09 15:09:11');
INSERT INTO `product_bom_headers` VALUES (112, '92751', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:09:17', '2026-04-09 15:09:17');
INSERT INTO `product_bom_headers` VALUES (115, '92371', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:09:39', '2026-04-09 15:09:39');
INSERT INTO `product_bom_headers` VALUES (116, '92381', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:09:46', '2026-04-09 15:09:46');
INSERT INTO `product_bom_headers` VALUES (117, '92391', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:09:52', '2026-04-09 15:09:52');
INSERT INTO `product_bom_headers` VALUES (118, '92401', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:10:03', '2026-04-09 15:10:03');
INSERT INTO `product_bom_headers` VALUES (119, '92411', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:10:10', '2026-04-09 15:10:10');
INSERT INTO `product_bom_headers` VALUES (120, '92421', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:10:17', '2026-04-09 15:10:17');
INSERT INTO `product_bom_headers` VALUES (121, '92431', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:10:28', '2026-04-09 15:10:28');
INSERT INTO `product_bom_headers` VALUES (122, '92441', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:10:40', '2026-04-09 15:10:40');
INSERT INTO `product_bom_headers` VALUES (123, '92331', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:35:12', '2026-04-09 15:35:12');
INSERT INTO `product_bom_headers` VALUES (124, '92332', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:35:17', '2026-04-09 15:35:17');
INSERT INTO `product_bom_headers` VALUES (125, '92442', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:37:21', '2026-04-09 15:37:21');
INSERT INTO `product_bom_headers` VALUES (126, '92451', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:37:46', '2026-04-09 15:37:46');
INSERT INTO `product_bom_headers` VALUES (127, '92461', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:37:55', '2026-04-09 15:37:55');
INSERT INTO `product_bom_headers` VALUES (128, '92471', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:38:03', '2026-04-09 15:38:03');
INSERT INTO `product_bom_headers` VALUES (129, '92481', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:38:14', '2026-04-09 15:38:14');
INSERT INTO `product_bom_headers` VALUES (130, '92511', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:38:23', '2026-04-09 15:38:23');
INSERT INTO `product_bom_headers` VALUES (131, '92521', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:38:31', '2026-04-09 15:38:31');
INSERT INTO `product_bom_headers` VALUES (132, '92531', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:38:38', '2026-04-09 15:38:38');
INSERT INTO `product_bom_headers` VALUES (133, '92541', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:38:47', '2026-04-09 15:38:47');
INSERT INTO `product_bom_headers` VALUES (134, '92551', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 15:38:57', '2026-04-09 15:38:57');
INSERT INTO `product_bom_headers` VALUES (135, '92561', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:07:07', '2026-04-09 16:07:07');
INSERT INTO `product_bom_headers` VALUES (136, '92571', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:07:20', '2026-04-09 16:07:20');
INSERT INTO `product_bom_headers` VALUES (137, '92581', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:07:26', '2026-04-09 16:07:26');
INSERT INTO `product_bom_headers` VALUES (138, '92591', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:07:34', '2026-04-09 16:07:34');
INSERT INTO `product_bom_headers` VALUES (139, '92601', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:08:17', '2026-04-09 16:08:17');
INSERT INTO `product_bom_headers` VALUES (140, '92611', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:08:27', '2026-04-09 16:08:27');
INSERT INTO `product_bom_headers` VALUES (141, '92651', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:09:41', '2026-04-09 16:09:41');
INSERT INTO `product_bom_headers` VALUES (142, '92661', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:09:54', '2026-04-09 16:09:54');
INSERT INTO `product_bom_headers` VALUES (143, '92671', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:10:22', '2026-04-09 16:10:22');
INSERT INTO `product_bom_headers` VALUES (144, '92691', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:10:50', '2026-04-09 16:10:50');
INSERT INTO `product_bom_headers` VALUES (145, '90931', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:11:04', '2026-04-09 16:11:04');
INSERT INTO `product_bom_headers` VALUES (146, '92781', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:11:18', '2026-04-09 16:11:18');
INSERT INTO `product_bom_headers` VALUES (147, '92841', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:11:34', '2026-04-09 16:11:34');
INSERT INTO `product_bom_headers` VALUES (148, '92881', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:11:48', '2026-04-09 16:11:48');
INSERT INTO `product_bom_headers` VALUES (149, '92891', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-09 16:11:59', '2026-04-09 16:11:59');
INSERT INTO `product_bom_headers` VALUES (150, '90411', 'production', '1', 'active', '2026-04-01', '2032-03-31', 1.0000, '個', NULL, 'zkily', 'zkily', '2026-04-20 14:31:41', '2026-04-20 14:31:41');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
