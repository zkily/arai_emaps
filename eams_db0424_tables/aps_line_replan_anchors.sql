SET NAMES utf8mb4;

CREATE TABLE `aps_line_replan_anchors`  (
  `line_id` int NOT NULL COMMENT 'machines.id',
  `anchor_date` date NOT NULL COMMENT '順次再計算の開始暦日（日本日付想定）',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`line_id`) USING BTREE,
  CONSTRAINT `fk_aps_line_replan_anchors_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '設備別再計算アンカー日' ROW_FORMAT = Dynamic;
INSERT INTO `aps_line_replan_anchors` VALUES (17, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (18, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (19, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (20, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (21, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (22, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (23, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (24, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (25, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (26, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (27, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (28, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (29, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (30, '2026-04-23', '2026-04-23 10:24:03');
INSERT INTO `aps_line_replan_anchors` VALUES (31, '2026-04-13', '2026-04-14 13:58:04');
INSERT INTO `aps_line_replan_anchors` VALUES (32, '2026-04-13', '2026-04-14 13:58:50');
INSERT INTO `aps_line_replan_anchors` VALUES (33, '2026-04-13', '2026-04-14 13:58:50');
INSERT INTO `aps_line_replan_anchors` VALUES (34, '2026-04-13', '2026-04-14 13:58:50');
INSERT INTO `aps_line_replan_anchors` VALUES (35, '2026-04-13', '2026-04-14 13:58:50');
INSERT INTO `aps_line_replan_anchors` VALUES (36, '2026-04-13', '2026-04-15 16:29:54');
INSERT INTO `aps_line_replan_anchors` VALUES (37, '2026-04-13', '2026-04-14 13:58:50');
INSERT INTO `aps_line_replan_anchors` VALUES (38, '2026-04-13', '2026-04-14 13:58:50');
INSERT INTO `aps_line_replan_anchors` VALUES (39, '2026-04-13', '2026-04-14 13:58:50');
INSERT INTO `aps_line_replan_anchors` VALUES (40, '2026-04-13', '2026-04-14 13:58:50');
INSERT INTO `aps_line_replan_anchors` VALUES (98, '2026-04-13', '2026-04-14 13:58:50');
