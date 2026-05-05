SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for production_plan_rate
-- ----------------------------
DROP TABLE IF EXISTS `production_plan_rate`;
CREATE TABLE `production_plan_rate`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ファイル名',
  `processed_at` datetime NOT NULL COMMENT '処理日時',
  `machine_cd` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備CD',
  `machine_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備名',
  `operation_variance` decimal(10, 2) NULL DEFAULT NULL COMMENT '操業度差異',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_file_name`(`file_name` ASC) USING BTREE,
  INDEX `idx_processed_at`(`processed_at` ASC) USING BTREE,
  INDEX `idx_machine_cd`(`machine_cd` ASC) USING BTREE,
  INDEX `idx_machine_name`(`machine_name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 62053 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '操業度データテーブル' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of production_plan_rate
-- ----------------------------
INSERT INTO `production_plan_rate` VALUES (37414, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-001', '成型01', 1.73, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37415, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-002', '成型02', 0.06, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37416, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-003', '成型03', -14.17, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37417, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-004', '成型04', 0.59, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37418, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-005', '成型05', 0.39, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37419, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-006', '成型06', -4.62, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37420, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-007', '成型07', 11.37, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37421, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-008', '成型08', -84.82, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37422, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-009', '成型09', -0.13, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37423, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-010', '成型10', -12.13, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37424, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-011', '成型11', -5.16, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37425, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-012', '成型12', 7.89, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37426, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-013', '成型13', 1.91, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37427, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-014', '成型14', 0.77, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37428, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-015', '成型15', -2.65, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37429, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-016', '成型16', 11.08, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37430, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-017', '成型17', -1.68, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37431, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-018', '成型18', 5.05, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37432, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-019', '成型19', 0.26, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37433, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-020', '成型20', 7.32, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37434, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-021', '成型21', 5.01, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37435, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-022', '成型22', -8.63, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37436, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-023', '成型23', 4.35, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37437, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-024', '成型24', 4.12, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37438, '加工計画(2月).xlsm', '2026-02-27 16:20:23', 'FM-025', '成型NC', 0.00, '2026-02-27 16:20:23', '2026-02-27 16:20:23');
INSERT INTO `production_plan_rate` VALUES (37497, '溶接計画(2月).xlsm', '2026-02-27 16:42:31', 'WL-001', '溶接01', 25.00, '2026-02-27 16:42:31', '2026-02-27 16:42:31');
INSERT INTO `production_plan_rate` VALUES (37498, '溶接計画(2月).xlsm', '2026-02-27 16:42:31', 'WL-002', '溶接02', 0.00, '2026-02-27 16:42:31', '2026-02-27 16:42:31');
INSERT INTO `production_plan_rate` VALUES (37499, '溶接計画(2月).xlsm', '2026-02-27 16:42:31', 'WL-003', '溶接03', NULL, '2026-02-27 16:42:31', '2026-02-27 16:42:31');
INSERT INTO `production_plan_rate` VALUES (37500, '溶接計画(2月).xlsm', '2026-02-27 16:42:31', 'WL-004', '溶接04', -4.00, '2026-02-27 16:42:31', '2026-02-27 16:42:31');
INSERT INTO `production_plan_rate` VALUES (37501, '溶接計画(2月).xlsm', '2026-02-27 16:42:31', 'WL-005', '溶接05', -4.00, '2026-02-27 16:42:31', '2026-02-27 16:42:31');
INSERT INTO `production_plan_rate` VALUES (37502, '溶接計画(2月).xlsm', '2026-02-27 16:42:31', 'WL-006', '溶接06', -8.00, '2026-02-27 16:42:31', '2026-02-27 16:42:31');
INSERT INTO `production_plan_rate` VALUES (37503, '溶接計画(2月).xlsm', '2026-02-27 16:42:31', 'WL-007', '溶接07', 0.00, '2026-02-27 16:42:31', '2026-02-27 16:42:31');
INSERT INTO `production_plan_rate` VALUES (37504, '溶接計画(2月).xlsm', '2026-02-27 16:42:31', 'WL-008', '溶接SP', 15.00, '2026-02-27 16:42:31', '2026-02-27 16:42:31');
INSERT INTO `production_plan_rate` VALUES (51552, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-001', '成型01', -11.01, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51553, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-002', '成型02', -17.34, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51554, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-003', '成型03', -11.25, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51555, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-004', '成型04', -2.87, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51556, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-005', '成型05', -6.04, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51557, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-006', '成型06', -26.62, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51558, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-007', '成型07', 3.95, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51559, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-008', '成型08', 0.00, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51560, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-009', '成型09', -15.69, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51561, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-010', '成型10', -15.74, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51562, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-011', '成型11', -1.85, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51563, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-012', '成型12', -3.88, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51564, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-013', '成型13', -18.77, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51565, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-014', '成型14', -4.11, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51566, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-015', '成型15', -12.52, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51567, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-016', '成型16', 7.01, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51568, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-017', '成型17', 0.00, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51569, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-018', '成型18', -2.51, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51570, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-019', '成型19', -4.65, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51571, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-020', '成型20', 4.99, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51572, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-021', '成型21', -1.85, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51573, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-022', '成型22', -9.19, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51574, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-023', '成型23', 11.53, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51575, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-024', '成型24', -2.41, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51576, '加工計画(3月).xlsm', '2026-03-31 15:20:48', 'FM-025', '成型NC', 0.00, '2026-03-31 15:20:48', '2026-03-31 15:20:48');
INSERT INTO `production_plan_rate` VALUES (51901, '溶接計画(3月).xlsm', '2026-03-31 18:03:29', 'WL-001', '溶接01', 10.00, '2026-03-31 18:03:29', '2026-03-31 18:03:29');
INSERT INTO `production_plan_rate` VALUES (51902, '溶接計画(3月).xlsm', '2026-03-31 18:03:29', 'WL-002', '溶接02', 0.00, '2026-03-31 18:03:29', '2026-03-31 18:03:29');
INSERT INTO `production_plan_rate` VALUES (51903, '溶接計画(3月).xlsm', '2026-03-31 18:03:29', 'WL-003', '溶接03', -13.00, '2026-03-31 18:03:29', '2026-03-31 18:03:29');
INSERT INTO `production_plan_rate` VALUES (51904, '溶接計画(3月).xlsm', '2026-03-31 18:03:29', 'WL-004', '溶接04', -21.00, '2026-03-31 18:03:29', '2026-03-31 18:03:29');
INSERT INTO `production_plan_rate` VALUES (51905, '溶接計画(3月).xlsm', '2026-03-31 18:03:29', 'WL-005', '溶接05', -13.00, '2026-03-31 18:03:29', '2026-03-31 18:03:29');
INSERT INTO `production_plan_rate` VALUES (51906, '溶接計画(3月).xlsm', '2026-03-31 18:03:29', 'WL-006', '溶接06', 0.00, '2026-03-31 18:03:29', '2026-03-31 18:03:29');
INSERT INTO `production_plan_rate` VALUES (51907, '溶接計画(3月).xlsm', '2026-03-31 18:03:29', 'WL-007', '溶接07', 0.00, '2026-03-31 18:03:29', '2026-03-31 18:03:29');
INSERT INTO `production_plan_rate` VALUES (51908, '溶接計画(3月).xlsm', '2026-03-31 18:03:29', 'WL-008', '溶接SP', 0.00, '2026-03-31 18:03:29', '2026-03-31 18:03:29');
INSERT INTO `production_plan_rate` VALUES (54642, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-001', '成型01', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54643, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-002', '成型02', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54644, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-003', '成型03', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54645, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-004', '成型04', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54646, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-005', '成型05', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54647, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-006', '成型06', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54648, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-007', '成型07', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54649, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-008', '成型08', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54650, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-009', '成型09', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54651, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-010', '成型10', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54652, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-011', '成型11', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54653, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-012', '成型12', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54654, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-013', '成型13', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54655, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-014', '成型14', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54656, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-015', '成型15', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54657, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-016', '成型16', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54658, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-017', '成型17', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54659, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-018', '成型18', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54660, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-019', '成型19', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54661, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-020', '成型20', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54662, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-021', '成型21', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54663, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-022', '成型22', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54664, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-023', '成型23', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54665, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-024', '成型24', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (54666, '加工計画(5月).xlsm', '2026-04-08 08:30:27', 'FM-025', '成型NC', 0.00, '2026-04-08 08:30:27', '2026-04-08 08:30:27');
INSERT INTO `production_plan_rate` VALUES (58148, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-001', '成型01', -2.78, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58149, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-002', '成型02', -4.96, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58150, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-003', '成型03', -2.19, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58151, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-004', '成型04', -0.92, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58152, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-005', '成型05', -2.94, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58153, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-006', '成型06', -2.29, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58154, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-007', '成型07', 3.96, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58155, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-008', '成型08', -10.81, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58156, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-009', '成型09', -16.41, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58157, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-010', '成型10', -6.26, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58158, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-011', '成型11', -1.74, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58159, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-012', '成型12', -4.80, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58160, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-013', '成型13', -9.74, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58161, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-014', '成型14', 6.52, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58162, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-015', '成型15', -6.66, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58163, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-016', '成型16', -14.01, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58164, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-017', '成型17', -1.98, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58165, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-018', '成型18', 5.46, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58166, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-019', '成型19', -3.65, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58167, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-020', '成型20', -5.47, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58168, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-021', '成型21', -0.94, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58169, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-022', '成型22', 4.30, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58170, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-023', '成型23', 8.79, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58171, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-024', '成型24', -7.52, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (58172, '加工計画(4月).xlsm', '2026-04-16 16:03:17', 'FM-025', '成型NC', 0.00, '2026-04-16 16:03:17', '2026-04-16 16:03:17');
INSERT INTO `production_plan_rate` VALUES (61925, '溶接計画(5月).xlsm', '2026-04-24 17:44:46', 'WL-001', '溶接01', 0.00, '2026-04-24 17:44:46', '2026-04-24 17:44:46');
INSERT INTO `production_plan_rate` VALUES (61926, '溶接計画(5月).xlsm', '2026-04-24 17:44:46', 'WL-002', '溶接02', 0.00, '2026-04-24 17:44:46', '2026-04-24 17:44:46');
INSERT INTO `production_plan_rate` VALUES (61927, '溶接計画(5月).xlsm', '2026-04-24 17:44:46', 'WL-003', '溶接03', 0.00, '2026-04-24 17:44:46', '2026-04-24 17:44:46');
INSERT INTO `production_plan_rate` VALUES (61928, '溶接計画(5月).xlsm', '2026-04-24 17:44:46', 'WL-004', '溶接04', 0.00, '2026-04-24 17:44:46', '2026-04-24 17:44:46');
INSERT INTO `production_plan_rate` VALUES (61929, '溶接計画(5月).xlsm', '2026-04-24 17:44:46', 'WL-005', '溶接05', 0.00, '2026-04-24 17:44:46', '2026-04-24 17:44:46');
INSERT INTO `production_plan_rate` VALUES (61930, '溶接計画(5月).xlsm', '2026-04-24 17:44:46', 'WL-006', '溶接06', 0.00, '2026-04-24 17:44:46', '2026-04-24 17:44:46');
INSERT INTO `production_plan_rate` VALUES (61931, '溶接計画(5月).xlsm', '2026-04-24 17:44:46', 'WL-007', '溶接07', 0.00, '2026-04-24 17:44:46', '2026-04-24 17:44:46');
INSERT INTO `production_plan_rate` VALUES (61932, '溶接計画(5月).xlsm', '2026-04-24 17:44:46', 'WL-008', '溶接SP', 0.00, '2026-04-24 17:44:46', '2026-04-24 17:44:46');
INSERT INTO `production_plan_rate` VALUES (62045, '溶接計画(4月).xlsm', '2026-04-28 14:27:22', 'WL-001', '溶接01', 3.00, '2026-04-28 14:27:22', '2026-04-28 14:27:22');
INSERT INTO `production_plan_rate` VALUES (62046, '溶接計画(4月).xlsm', '2026-04-28 14:27:22', 'WL-002', '溶接02', 15.00, '2026-04-28 14:27:22', '2026-04-28 14:27:22');
INSERT INTO `production_plan_rate` VALUES (62047, '溶接計画(4月).xlsm', '2026-04-28 14:27:22', 'WL-003', '溶接03', -13.00, '2026-04-28 14:27:22', '2026-04-28 14:27:22');
INSERT INTO `production_plan_rate` VALUES (62048, '溶接計画(4月).xlsm', '2026-04-28 14:27:22', 'WL-004', '溶接04', -11.00, '2026-04-28 14:27:22', '2026-04-28 14:27:22');
INSERT INTO `production_plan_rate` VALUES (62049, '溶接計画(4月).xlsm', '2026-04-28 14:27:22', 'WL-005', '溶接05', -10.00, '2026-04-28 14:27:22', '2026-04-28 14:27:22');
INSERT INTO `production_plan_rate` VALUES (62050, '溶接計画(4月).xlsm', '2026-04-28 14:27:22', 'WL-006', '溶接06', -16.00, '2026-04-28 14:27:22', '2026-04-28 14:27:22');
INSERT INTO `production_plan_rate` VALUES (62051, '溶接計画(4月).xlsm', '2026-04-28 14:27:22', 'WL-007', '溶接07', 0.00, '2026-04-28 14:27:22', '2026-04-28 14:27:22');
INSERT INTO `production_plan_rate` VALUES (62052, '溶接計画(4月).xlsm', '2026-04-28 14:27:22', 'WL-008', '溶接SP', -11.00, '2026-04-28 14:27:22', '2026-04-28 14:27:22');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
