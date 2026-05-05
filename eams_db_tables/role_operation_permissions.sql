SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for role_operation_permissions
-- ----------------------------
DROP TABLE IF EXISTS `role_operation_permissions`;
CREATE TABLE `role_operation_permissions`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_id` int NOT NULL COMMENT 'ロールID',
  `module` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'モジュール名',
  `can_create` tinyint(1) NULL DEFAULT 0 COMMENT '新規作成権限',
  `can_edit` tinyint(1) NULL DEFAULT 0 COMMENT '編集権限',
  `can_delete` tinyint(1) NULL DEFAULT 0 COMMENT '削除権限',
  `can_export` tinyint(1) NULL DEFAULT 0 COMMENT '出力権限',
  `can_approve` tinyint(1) NULL DEFAULT 0 COMMENT '承認権限',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_role_module`(`role_id` ASC, `module` ASC) USING BTREE,
  INDEX `idx_rop_role`(`role_id` ASC) USING BTREE,
  CONSTRAINT `fk_rop_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 141 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'ロール・操作権限テーブル' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of role_operation_permissions
-- ----------------------------
INSERT INTO `role_operation_permissions` VALUES (85, 9, '販売管理', 0, 0, 0, 0, 0, '2026-02-06 11:28:24', '2026-02-06 11:28:24');
INSERT INTO `role_operation_permissions` VALUES (86, 9, '購買管理', 0, 0, 0, 0, 0, '2026-02-06 11:28:24', '2026-02-06 11:28:24');
INSERT INTO `role_operation_permissions` VALUES (87, 9, '在庫管理', 0, 0, 0, 0, 0, '2026-02-06 11:28:24', '2026-02-06 11:28:24');
INSERT INTO `role_operation_permissions` VALUES (88, 9, '原価・会計', 0, 0, 0, 0, 0, '2026-02-06 11:28:24', '2026-02-06 11:28:24');
INSERT INTO `role_operation_permissions` VALUES (89, 9, '生産計画', 0, 0, 0, 0, 0, '2026-02-06 11:28:24', '2026-02-06 11:28:24');
INSERT INTO `role_operation_permissions` VALUES (90, 9, '製造実行', 0, 0, 0, 0, 0, '2026-02-06 11:28:24', '2026-02-06 11:28:24');
INSERT INTO `role_operation_permissions` VALUES (91, 9, '品質管理', 0, 0, 0, 0, 0, '2026-02-06 11:28:24', '2026-02-06 11:28:24');
INSERT INTO `role_operation_permissions` VALUES (92, 9, 'システム管理', 0, 0, 0, 0, 0, '2026-02-06 11:28:24', '2026-02-06 11:28:24');
INSERT INTO `role_operation_permissions` VALUES (109, 7, '販売管理', 1, 1, 1, 1, 1, '2026-02-09 09:59:06', '2026-02-09 09:59:06');
INSERT INTO `role_operation_permissions` VALUES (110, 7, '購買管理', 1, 1, 1, 1, 1, '2026-02-09 09:59:06', '2026-02-09 09:59:06');
INSERT INTO `role_operation_permissions` VALUES (111, 7, '在庫管理', 1, 1, 1, 1, 1, '2026-02-09 09:59:06', '2026-02-09 09:59:06');
INSERT INTO `role_operation_permissions` VALUES (112, 7, '原価・会計', 1, 1, 1, 1, 1, '2026-02-09 09:59:06', '2026-02-09 09:59:06');
INSERT INTO `role_operation_permissions` VALUES (113, 7, '生産計画', 1, 1, 1, 1, 1, '2026-02-09 09:59:06', '2026-02-09 09:59:06');
INSERT INTO `role_operation_permissions` VALUES (114, 7, '製造実行', 1, 1, 1, 1, 1, '2026-02-09 09:59:06', '2026-02-09 09:59:06');
INSERT INTO `role_operation_permissions` VALUES (115, 7, '品質管理', 1, 1, 1, 1, 1, '2026-02-09 09:59:06', '2026-02-09 09:59:06');
INSERT INTO `role_operation_permissions` VALUES (116, 7, 'システム管理', 0, 0, 0, 0, 0, '2026-02-09 09:59:06', '2026-02-09 09:59:06');
INSERT INTO `role_operation_permissions` VALUES (117, 2, '販売管理', 1, 1, 0, 1, 0, '2026-04-16 13:03:44', '2026-04-16 13:03:44');
INSERT INTO `role_operation_permissions` VALUES (118, 2, '購買管理', 1, 1, 0, 1, 0, '2026-04-16 13:03:44', '2026-04-16 13:03:44');
INSERT INTO `role_operation_permissions` VALUES (119, 2, '在庫管理', 1, 1, 0, 1, 0, '2026-04-16 13:03:44', '2026-04-16 13:03:44');
INSERT INTO `role_operation_permissions` VALUES (120, 2, '原価・会計', 1, 1, 0, 1, 0, '2026-04-16 13:03:44', '2026-04-16 13:03:44');
INSERT INTO `role_operation_permissions` VALUES (121, 2, '生産計画', 1, 1, 0, 1, 0, '2026-04-16 13:03:44', '2026-04-16 13:03:44');
INSERT INTO `role_operation_permissions` VALUES (122, 2, '製造実行', 1, 1, 0, 1, 0, '2026-04-16 13:03:44', '2026-04-16 13:03:44');
INSERT INTO `role_operation_permissions` VALUES (123, 2, '品質管理', 1, 1, 0, 1, 0, '2026-04-16 13:03:44', '2026-04-16 13:03:44');
INSERT INTO `role_operation_permissions` VALUES (124, 2, 'システム管理', 0, 0, 0, 0, 0, '2026-04-16 13:03:44', '2026-04-16 13:03:44');
INSERT INTO `role_operation_permissions` VALUES (125, 8, '販売管理', 1, 1, 0, 1, 0, '2026-04-16 13:04:24', '2026-04-16 13:04:24');
INSERT INTO `role_operation_permissions` VALUES (126, 8, '購買管理', 1, 1, 0, 1, 0, '2026-04-16 13:04:24', '2026-04-16 13:04:24');
INSERT INTO `role_operation_permissions` VALUES (127, 8, '在庫管理', 1, 1, 0, 1, 0, '2026-04-16 13:04:24', '2026-04-16 13:04:24');
INSERT INTO `role_operation_permissions` VALUES (128, 8, '原価・会計', 1, 1, 0, 1, 0, '2026-04-16 13:04:24', '2026-04-16 13:04:24');
INSERT INTO `role_operation_permissions` VALUES (129, 8, '生産計画', 1, 1, 0, 1, 0, '2026-04-16 13:04:24', '2026-04-16 13:04:24');
INSERT INTO `role_operation_permissions` VALUES (130, 8, '製造実行', 1, 1, 0, 1, 0, '2026-04-16 13:04:24', '2026-04-16 13:04:24');
INSERT INTO `role_operation_permissions` VALUES (131, 8, '品質管理', 1, 1, 0, 1, 0, '2026-04-16 13:04:24', '2026-04-16 13:04:24');
INSERT INTO `role_operation_permissions` VALUES (132, 8, 'システム管理', 0, 0, 0, 0, 0, '2026-04-16 13:04:24', '2026-04-16 13:04:24');
INSERT INTO `role_operation_permissions` VALUES (133, 1, '販売管理', 1, 1, 1, 1, 1, '2026-04-16 13:05:41', '2026-04-16 13:05:41');
INSERT INTO `role_operation_permissions` VALUES (134, 1, '購買管理', 1, 1, 1, 1, 1, '2026-04-16 13:05:41', '2026-04-16 13:05:41');
INSERT INTO `role_operation_permissions` VALUES (135, 1, '在庫管理', 1, 1, 1, 1, 1, '2026-04-16 13:05:41', '2026-04-16 13:05:41');
INSERT INTO `role_operation_permissions` VALUES (136, 1, '原価・会計', 1, 1, 1, 1, 1, '2026-04-16 13:05:41', '2026-04-16 13:05:41');
INSERT INTO `role_operation_permissions` VALUES (137, 1, '生産計画', 1, 1, 1, 1, 1, '2026-04-16 13:05:41', '2026-04-16 13:05:41');
INSERT INTO `role_operation_permissions` VALUES (138, 1, '製造実行', 1, 1, 1, 1, 1, '2026-04-16 13:05:41', '2026-04-16 13:05:41');
INSERT INTO `role_operation_permissions` VALUES (139, 1, '品質管理', 1, 1, 1, 1, 1, '2026-04-16 13:05:41', '2026-04-16 13:05:41');
INSERT INTO `role_operation_permissions` VALUES (140, 1, 'システム管理', 1, 1, 1, 1, 1, '2026-04-16 13:05:41', '2026-04-16 13:05:41');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
