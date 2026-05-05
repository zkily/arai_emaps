SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for destination_workdays
-- ----------------------------
DROP TABLE IF EXISTS `destination_workdays`;
CREATE TABLE `destination_workdays`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先マスタCD\r\n',
  `work_date` date NOT NULL COMMENT '土日の出勤日',
  `reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '理由',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_work_day`(`destination_cd` ASC, `work_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 12 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '納入先臨時出勤日マスタ（休日例外）' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of destination_workdays
-- ----------------------------
INSERT INTO `destination_workdays` VALUES (1, 'N08', '2025-05-02', '', '2025-04-26 08:12:18');
INSERT INTO `destination_workdays` VALUES (2, 'N08', '2025-05-09', '456', '2025-04-26 08:13:54');
INSERT INTO `destination_workdays` VALUES (3, 'N14', '2025-07-05', '', '2025-06-25 18:50:24');
INSERT INTO `destination_workdays` VALUES (4, 'N14', '2025-07-19', '', '2025-07-04 15:35:31');
INSERT INTO `destination_workdays` VALUES (5, 'N14', '2025-08-02', '', '2025-07-21 10:35:53');
INSERT INTO `destination_workdays` VALUES (6, 'N14', '2025-08-23', '', '2025-08-01 16:50:09');
INSERT INTO `destination_workdays` VALUES (7, 'N14', '2025-09-06', '', '2025-08-22 16:07:28');
INSERT INTO `destination_workdays` VALUES (8, 'N14', '2025-09-20', '', '2025-09-05 16:20:35');
INSERT INTO `destination_workdays` VALUES (9, 'N14', '2025-10-04', '', '2025-09-19 16:29:59');
INSERT INTO `destination_workdays` VALUES (10, 'N14', '2026-02-07', '', '2026-01-23 16:53:58');
INSERT INTO `destination_workdays` VALUES (11, 'N14', '2026-02-21', '', '2026-02-09 10:39:55');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
