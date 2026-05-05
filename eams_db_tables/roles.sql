SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for roles
-- ----------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ロール名',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '説明',
  `is_system` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'システムロールフラグ（1:削除不可）',
  `data_scope` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'department' COMMENT 'データ参照範囲（self/department/department_below/all/custom）',
  `custom_departments` json NULL COMMENT 'カスタム部門リスト（data_scope=customの場合）',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'ロールテーブル' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of roles
-- ----------------------------
INSERT INTO `roles` VALUES (1, '管理者', 'システム管理者（全権限）', 1, 'all', NULL, 1, '2026-02-05 14:00:55', '2026-02-05 14:00:55');
INSERT INTO `roles` VALUES (2, '一般ユーザー', '一般ユーザー（読み書き権限）', 1, 'department', NULL, 1, '2026-02-05 14:00:55', '2026-02-05 14:00:55');
INSERT INTO `roles` VALUES (7, 'マネージャー', 'システム使用者（全権限）', 1, 'all', 'null', 1, '2026-02-05 16:43:34', '2026-02-06 10:33:48');
INSERT INTO `roles` VALUES (8, '作業者', 'システム使用者（一部権限）', 1, 'department', 'null', 1, '2026-02-05 16:43:55', '2026-02-06 10:34:15');
INSERT INTO `roles` VALUES (9, 'ゲスト', '閲覧のみ', 0, 'all', 'null', 1, '2026-02-05 16:48:09', '2026-02-05 16:51:05');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
