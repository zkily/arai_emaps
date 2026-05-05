SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for machines
-- ----------------------------
DROP TABLE IF EXISTS `machines`;
CREATE TABLE `machines`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '设备ID',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '设备CD',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '设备名称',
  `machine_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '设备种类（例：切断、焊接、检査等）',
  `default_work_hours` decimal(4, 2) NULL DEFAULT NULL COMMENT '基準稼働時間（時間）',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '有効フラグ',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT 'active' COMMENT '状态（active/inactive/maintenance）',
  `available_from` time NULL DEFAULT '08:00:00' COMMENT '可用开始时间',
  `available_to` time NULL DEFAULT '17:00:00' COMMENT '可用结束时间',
  `calendar_id` int NULL DEFAULT NULL COMMENT '所属カレンダーID（处理休假）',
  `efficiency` decimal(5, 2) NULL DEFAULT 100.00 COMMENT '效率（基准为100）',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '备注',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `machine_cd`(`machine_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 116 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin COMMENT = '設備マスタ' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of machines
-- ----------------------------
INSERT INTO `machines` VALUES (1, 'CUT-001', '切断01', '切断', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 95.00, NULL, '2025-05-21 14:02:33', '2025-05-21 14:25:06');
INSERT INTO `machines` VALUES (2, 'CUT-002', '切断02', '切断', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 95.00, NULL, '2025-05-21 14:23:22', '2025-05-21 14:25:06');
INSERT INTO `machines` VALUES (3, 'CUT-003', '切断03', '切断', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 94.00, NULL, '2025-05-21 14:23:39', '2025-05-21 14:25:07');
INSERT INTO `machines` VALUES (4, 'CUT-004', '切断04', '切断', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 95.00, NULL, '2025-05-21 14:23:52', '2025-05-21 14:25:07');
INSERT INTO `machines` VALUES (6, 'CUT-005', '切断05', '切断', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 95.00, NULL, '2025-05-21 14:24:16', '2025-05-21 14:25:13');
INSERT INTO `machines` VALUES (7, 'CH-001', '面取01', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:27:51', '2025-05-23 13:32:56');
INSERT INTO `machines` VALUES (8, 'CH-002', '面取02', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:28:01', '2025-05-23 13:32:59');
INSERT INTO `machines` VALUES (9, 'CH-003', '面取03', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:28:07', '2025-05-23 13:33:00');
INSERT INTO `machines` VALUES (10, 'CH-004', '面取04', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:28:13', '2025-05-23 13:33:01');
INSERT INTO `machines` VALUES (11, 'CH-005', '面取05', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:28:20', '2025-05-23 13:33:01');
INSERT INTO `machines` VALUES (12, 'CH-006', '面取06', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:28:27', '2025-05-23 13:33:02');
INSERT INTO `machines` VALUES (13, 'CH-007', '面取07', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:28:34', '2025-05-23 13:33:03');
INSERT INTO `machines` VALUES (14, 'CH-008', '面取08', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:28:40', '2025-05-23 13:33:03');
INSERT INTO `machines` VALUES (15, 'CH-009', '面取09', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:28:48', '2025-05-23 13:33:04');
INSERT INTO `machines` VALUES (16, 'CH-010', '面取10', '面取', NULL, NULL, 'active', '00:00:00', '23:59:59', NULL, 96.00, NULL, '2025-05-21 14:28:55', '2025-05-23 13:33:06');
INSERT INTO `machines` VALUES (17, 'FM-001', '成型01', '成型', NULL, NULL, 'active', '00:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:35:13', '2025-05-21 14:38:20');
INSERT INTO `machines` VALUES (18, 'FM-002', '成型02', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:35:22', '2025-05-21 14:35:22');
INSERT INTO `machines` VALUES (19, 'FM-003', '成型03', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:35:28', '2025-05-21 14:35:28');
INSERT INTO `machines` VALUES (20, 'FM-004', '成型04', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:35:35', '2025-05-21 14:35:35');
INSERT INTO `machines` VALUES (21, 'FM-005', '成型05', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:35:41', '2025-05-21 14:35:41');
INSERT INTO `machines` VALUES (22, 'FM-006', '成型06', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:35:47', '2025-05-21 14:35:47');
INSERT INTO `machines` VALUES (23, 'FM-007', '成型07', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:35:53', '2025-05-21 14:35:53');
INSERT INTO `machines` VALUES (24, 'FM-008', '成型08', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:35:59', '2025-05-21 14:35:59');
INSERT INTO `machines` VALUES (25, 'FM-009', '成型09', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:36:05', '2025-05-21 14:36:05');
INSERT INTO `machines` VALUES (26, 'FM-010', '成型10', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:36:12', '2025-05-21 14:36:12');
INSERT INTO `machines` VALUES (27, 'FM-011', '成型11', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:36:18', '2025-05-21 14:36:18');
INSERT INTO `machines` VALUES (28, 'FM-012', '成型12', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:36:25', '2025-05-21 14:36:25');
INSERT INTO `machines` VALUES (29, 'FM-013', '成型13', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:36:30', '2025-05-21 14:36:30');
INSERT INTO `machines` VALUES (30, 'FM-014', '成型14', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:36:36', '2025-05-21 14:36:36');
INSERT INTO `machines` VALUES (31, 'FM-015', '成型15', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:36:42', '2025-05-21 14:36:42');
INSERT INTO `machines` VALUES (32, 'FM-016', '成型16', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:36:49', '2025-05-21 14:36:49');
INSERT INTO `machines` VALUES (33, 'FM-017', '成型17', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:36:55', '2025-05-21 14:36:55');
INSERT INTO `machines` VALUES (34, 'FM-018', '成型18', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:37:00', '2025-05-21 14:37:00');
INSERT INTO `machines` VALUES (35, 'FM-019', '成型19', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:37:06', '2025-05-21 14:37:06');
INSERT INTO `machines` VALUES (36, 'FM-020', '成型20', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:37:14', '2025-05-21 14:37:14');
INSERT INTO `machines` VALUES (37, 'FM-021', '成型21', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:37:20', '2025-05-21 14:37:20');
INSERT INTO `machines` VALUES (38, 'FM-022', '成型22', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:37:25', '2025-05-21 14:37:25');
INSERT INTO `machines` VALUES (39, 'FM-023', '成型23', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:37:32', '2025-05-21 14:37:32');
INSERT INTO `machines` VALUES (40, 'FM-024', '成型24', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 95.00, NULL, '2025-05-21 14:37:41', '2026-04-08 10:32:01');
INSERT INTO `machines` VALUES (41, 'PL-001', '三次元4段', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:09:58', '2025-05-23 13:09:58');
INSERT INTO `machines` VALUES (42, 'PL-002', '三次元3段', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:10:18', '2025-05-23 13:10:18');
INSERT INTO `machines` VALUES (43, 'PL-003', 'J曲3段', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:10:51', '2025-05-23 13:10:51');
INSERT INTO `machines` VALUES (44, 'PL-004', 'J曲4段', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:11:07', '2025-05-23 13:11:07');
INSERT INTO `machines` VALUES (45, 'PL-005', 'J曲5段', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:11:18', '2025-05-23 13:11:18');
INSERT INTO `machines` VALUES (46, 'PL-006', 'コの字3段', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:12:06', '2025-05-23 13:12:06');
INSERT INTO `machines` VALUES (47, 'PL-007', 'コの字4段', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:12:21', '2025-05-23 13:12:21');
INSERT INTO `machines` VALUES (48, 'PL-008', '16本治具', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:12:47', '2025-05-23 13:12:47');
INSERT INTO `machines` VALUES (49, 'PL-009', '091D FR', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:13:10', '2025-05-23 13:13:10');
INSERT INTO `machines` VALUES (50, 'PL-010', '120D 3RD', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:13:30', '2025-05-23 13:13:30');
INSERT INTO `machines` VALUES (51, 'PL-011', '3X45 CTR', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:13:56', '2025-05-23 13:13:56');
INSERT INTO `machines` VALUES (52, 'PL-012', '310B CTR', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:14:10', '2025-05-23 13:14:10');
INSERT INTO `machines` VALUES (53, 'PL-013', '400A CTR', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:14:23', '2025-05-23 13:14:23');
INSERT INTO `machines` VALUES (54, 'PL-014', '670B 3RD CTR', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:14:51', '2025-05-23 13:14:51');
INSERT INTO `machines` VALUES (55, 'PL-015', '670B 3RD SIDE', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:15:01', '2025-05-23 13:15:01');
INSERT INTO `machines` VALUES (56, 'PL-016', '668A RR アーチ', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:15:34', '2025-05-23 13:15:34');
INSERT INTO `machines` VALUES (57, 'PL-017', '720B RR SD', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:16:05', '2025-05-23 13:16:05');
INSERT INTO `machines` VALUES (58, 'PL-018', 'XC2A FR', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:16:36', '2025-05-23 13:16:36');
INSERT INTO `machines` VALUES (59, 'PL-019', 'XC2A RR', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:16:48', '2025-05-23 13:16:48');
INSERT INTO `machines` VALUES (60, 'PL-020', 'XC2B LH', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:17:23', '2025-05-23 13:17:23');
INSERT INTO `machines` VALUES (61, 'PL-021', 'X61G 3RD', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:17:47', '2025-05-23 13:17:47');
INSERT INTO `machines` VALUES (62, 'PL-022', 'レッグ', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:18:09', '2025-05-23 13:18:09');
INSERT INTO `machines` VALUES (63, 'PL-023', 'スライディング', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:18:24', '2025-05-23 13:18:24');
INSERT INTO `machines` VALUES (64, 'PL-024', 'ブラケット', 'メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-05-23 13:18:41', '2025-05-23 13:18:41');
INSERT INTO `machines` VALUES (65, 'WL-001', '溶接01', '溶接', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:21:32', '2025-05-23 13:21:32');
INSERT INTO `machines` VALUES (66, 'WL-002', '溶接02', '溶接', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:21:46', '2025-05-23 13:21:46');
INSERT INTO `machines` VALUES (67, 'WL-003', '溶接03', '溶接', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:21:52', '2025-05-23 13:21:52');
INSERT INTO `machines` VALUES (68, 'WL-004', '溶接04', '溶接', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:21:58', '2025-05-23 13:21:58');
INSERT INTO `machines` VALUES (69, 'WL-005', '溶接05', '溶接', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:22:03', '2025-05-23 13:22:03');
INSERT INTO `machines` VALUES (70, 'WL-006', '溶接06', '溶接', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:22:10', '2025-05-23 13:22:10');
INSERT INTO `machines` VALUES (72, 'WL-008', '溶接SP', '溶接', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:22:30', '2025-05-23 13:22:30');
INSERT INTO `machines` VALUES (73, 'IN-001', '検査01', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:34:36', '2025-05-23 13:34:36');
INSERT INTO `machines` VALUES (75, 'IN-002', '検査02', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:00', '2025-05-23 13:35:00');
INSERT INTO `machines` VALUES (76, 'IN-003', '検査03', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:05', '2025-05-23 13:35:05');
INSERT INTO `machines` VALUES (77, 'IN-004', '検査04', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:11', '2025-05-23 13:35:11');
INSERT INTO `machines` VALUES (78, 'IN-005', '検査05', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:15', '2025-05-23 13:35:15');
INSERT INTO `machines` VALUES (79, 'IN-006', '検査06', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:20', '2025-05-23 13:35:20');
INSERT INTO `machines` VALUES (80, 'IN-007', '検査07', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:24', '2025-05-23 13:35:24');
INSERT INTO `machines` VALUES (81, 'IN-008', '検査08', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:29', '2025-05-23 13:35:29');
INSERT INTO `machines` VALUES (82, 'IN-009', '検査09', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:34', '2025-05-23 13:35:34');
INSERT INTO `machines` VALUES (83, 'IN-010', '検査10', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:39', '2025-05-23 13:35:39');
INSERT INTO `machines` VALUES (84, 'IN-011', '検査11', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:45', '2025-05-23 13:35:45');
INSERT INTO `machines` VALUES (85, 'IN-012', '検査12', '検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-05-23 13:35:49', '2025-05-23 13:35:49');
INSERT INTO `machines` VALUES (88, 'OT-001', '外注切断', '外注切断', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-06-02 15:58:35', '2025-06-02 15:58:35');
INSERT INTO `machines` VALUES (91, 'IN-013', '溶接前検査13', '溶接前検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-06-02 18:27:31', '2025-06-02 18:27:31');
INSERT INTO `machines` VALUES (92, 'IN-014', '溶接前検査14', '溶接前検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-06-02 18:27:42', '2025-06-02 18:27:42');
INSERT INTO `machines` VALUES (93, 'IN-015', '溶接前検査15', '溶接前検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 92.00, NULL, '2025-06-02 18:27:48', '2025-06-02 18:27:48');
INSERT INTO `machines` VALUES (94, 'OT-002', '外注成型', '外注成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-06-03 10:20:30', '2025-06-03 10:20:30');
INSERT INTO `machines` VALUES (95, 'OT-003', '外注メッキ', '外注メッキ', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-06-03 10:20:47', '2025-06-03 10:20:47');
INSERT INTO `machines` VALUES (96, 'OT-004', '外注溶接', '外注溶接', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-06-03 10:21:01', '2025-06-03 10:21:01');
INSERT INTO `machines` VALUES (97, 'OT-005', '外注検査', '外注検査', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 100.00, NULL, '2025-06-03 10:21:14', '2025-06-03 10:21:14');
INSERT INTO `machines` VALUES (98, 'FM-025', '成型NC', '成型', NULL, NULL, 'active', '08:00:00', '17:00:00', NULL, 90.00, NULL, '2025-06-03 10:40:11', '2025-06-03 10:40:11');
INSERT INTO `machines` VALUES (114, 'FM-026', '成型他', '成型', NULL, NULL, 'active', NULL, NULL, NULL, 100.00, NULL, '2026-02-24 18:58:56', '2026-02-24 18:58:56');
INSERT INTO `machines` VALUES (115, 'CUT-006', '切断06', '切断', NULL, NULL, 'active', '00:00:50', '23:59:50', NULL, 95.00, 'レーザー切断', '2026-04-27 18:32:43', '2026-04-27 18:33:20');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
