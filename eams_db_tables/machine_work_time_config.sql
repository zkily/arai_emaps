SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for machine_work_time_config
-- ----------------------------
DROP TABLE IF EXISTS `machine_work_time_config`;
CREATE TABLE `machine_work_time_config`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `time_slot_17_19` tinyint(1) NULL DEFAULT 0 COMMENT '17-19时间段是否运行',
  `time_slot_19_21` tinyint(1) NULL DEFAULT 0 COMMENT '19-21时间段是否运行',
  `time_slot_6_8` tinyint(1) NULL DEFAULT 0 COMMENT '6-8时间段是否运行',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`, `machine_cd`, `machine_name`) USING BTREE,
  UNIQUE INDEX `unique_machine`(`machine_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 267 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of machine_work_time_config
-- ----------------------------
INSERT INTO `machine_work_time_config` VALUES (2, 'FM-001', '成型01', 1, 1, 1, '2025-11-07 17:33:59', '2026-01-30 14:53:09');
INSERT INTO `machine_work_time_config` VALUES (3, 'FM-002', '成型02', 1, 1, 0, '2025-11-07 17:35:07', '2026-03-12 11:28:17');
INSERT INTO `machine_work_time_config` VALUES (4, 'FM-003', '成型03', 0, 0, 0, '2025-11-07 17:37:30', '2026-03-05 16:31:14');
INSERT INTO `machine_work_time_config` VALUES (5, 'FM-004', '成型04', 0, 0, 0, '2025-11-07 17:37:38', '2026-03-30 15:44:41');
INSERT INTO `machine_work_time_config` VALUES (6, 'FM-005', '成型05', 0, 0, 0, '2025-11-07 17:37:42', '2026-03-05 16:31:14');
INSERT INTO `machine_work_time_config` VALUES (7, 'FM-006', '成型06', 1, 1, 0, '2025-11-07 17:37:45', '2026-03-30 15:44:41');
INSERT INTO `machine_work_time_config` VALUES (8, 'FM-007', '成型07', 0, 0, 0, '2025-11-07 17:37:49', '2026-01-30 14:53:09');
INSERT INTO `machine_work_time_config` VALUES (9, 'FM-008', '成型08', 1, 1, 0, '2025-11-07 17:37:52', '2026-03-12 11:28:17');
INSERT INTO `machine_work_time_config` VALUES (10, 'FM-009', '成型09', 0, 0, 0, '2025-11-07 17:37:55', '2026-01-30 14:53:09');
INSERT INTO `machine_work_time_config` VALUES (11, 'FM-010', '成型10', 1, 1, 1, '2025-11-07 17:37:59', '2026-03-30 15:44:41');
INSERT INTO `machine_work_time_config` VALUES (12, 'FM-011', '成型11', 1, 1, 1, '2025-11-07 17:38:04', '2026-01-30 14:53:09');
INSERT INTO `machine_work_time_config` VALUES (13, 'FM-012', '成型12', 0, 0, 0, '2025-11-07 17:38:10', '2026-01-30 14:53:09');
INSERT INTO `machine_work_time_config` VALUES (14, 'FM-013', '成型13', 1, 1, 1, '2025-11-07 17:38:14', '2026-03-30 15:44:41');
INSERT INTO `machine_work_time_config` VALUES (15, 'FM-014', '成型14', 0, 0, 0, '2025-11-07 17:38:17', '2026-01-30 14:53:09');
INSERT INTO `machine_work_time_config` VALUES (16, 'FM-015', '成型15', 0, 0, 0, '2025-11-07 17:38:23', '2026-03-12 11:26:39');
INSERT INTO `machine_work_time_config` VALUES (32, 'FM-016', '成型16', 0, 0, 0, '2025-11-07 17:38:51', '2026-03-12 11:26:39');
INSERT INTO `machine_work_time_config` VALUES (33, 'FM-017', '成型17', 0, 0, 0, '2025-11-07 17:38:54', '2026-01-30 14:53:09');
INSERT INTO `machine_work_time_config` VALUES (34, 'FM-018', '成型18', 1, 1, 0, '2025-11-07 17:38:57', '2026-03-12 11:28:17');
INSERT INTO `machine_work_time_config` VALUES (35, 'FM-019', '成型19', 0, 0, 0, '2025-11-07 17:39:00', '2026-01-30 14:53:09');
INSERT INTO `machine_work_time_config` VALUES (36, 'FM-020', '成型20', 0, 0, 0, '2025-11-07 17:39:04', '2026-03-05 16:31:14');
INSERT INTO `machine_work_time_config` VALUES (37, 'FM-021', '成型21', 0, 0, 0, '2025-11-07 17:39:07', '2026-01-30 14:53:09');
INSERT INTO `machine_work_time_config` VALUES (38, 'FM-022', '成型22', 0, 0, 0, '2025-11-07 17:39:10', '2026-03-05 16:31:14');
INSERT INTO `machine_work_time_config` VALUES (39, 'FM-023', '成型23', 1, 1, 1, '2025-11-07 17:39:13', '2026-03-30 15:44:41');
INSERT INTO `machine_work_time_config` VALUES (40, 'FM-024', '成型24', 0, 0, 0, '2025-11-07 17:39:16', '2026-03-30 15:44:41');
INSERT INTO `machine_work_time_config` VALUES (41, 'FM-025', '成型NC', 0, 0, 0, '2025-11-07 17:39:21', '2026-01-30 14:53:09');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
