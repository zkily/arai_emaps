SET NAMES utf8mb4;

CREATE TABLE `user_roles`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT 'ユーザーID',
  `role_id` int NOT NULL COMMENT 'ロールID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_role`(`user_id` ASC, `role_id` ASC) USING BTREE,
  INDEX `idx_user_roles_user`(`user_id` ASC) USING BTREE,
  INDEX `idx_user_roles_role`(`role_id` ASC) USING BTREE,
  CONSTRAINT `fk_ur_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_ur_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 36 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'ユーザー・ロール関連テーブル' ROW_FORMAT = Dynamic;
INSERT INTO `user_roles` VALUES (6, 2, 1, '2026-02-06 10:42:16');
INSERT INTO `user_roles` VALUES (7, 3, 1, '2026-02-06 10:42:33');
INSERT INTO `user_roles` VALUES (11, 7, 2, '2026-02-06 10:49:24');
INSERT INTO `user_roles` VALUES (12, 8, 2, '2026-02-06 10:50:12');
INSERT INTO `user_roles` VALUES (15, 4, 8, '2026-02-06 11:08:37');
INSERT INTO `user_roles` VALUES (16, 6, 7, '2026-02-06 11:08:47');
INSERT INTO `user_roles` VALUES (17, 5, 7, '2026-02-06 11:08:52');
INSERT INTO `user_roles` VALUES (18, 9, 2, '2026-02-19 08:20:04');
INSERT INTO `user_roles` VALUES (20, 11, 8, '2026-03-31 17:30:50');
INSERT INTO `user_roles` VALUES (21, 12, 8, '2026-03-31 17:31:30');
INSERT INTO `user_roles` VALUES (22, 13, 8, '2026-03-31 17:32:14');
INSERT INTO `user_roles` VALUES (23, 14, 7, '2026-04-01 11:19:39');
INSERT INTO `user_roles` VALUES (24, 15, 7, '2026-04-02 16:43:49');
INSERT INTO `user_roles` VALUES (25, 16, 2, '2026-04-02 17:06:20');
INSERT INTO `user_roles` VALUES (26, 17, 7, '2026-04-02 18:06:55');
INSERT INTO `user_roles` VALUES (27, 10, 7, '2026-04-02 18:07:33');
INSERT INTO `user_roles` VALUES (28, 18, 7, '2026-04-02 18:08:26');
INSERT INTO `user_roles` VALUES (29, 19, 7, '2026-04-02 18:09:18');
INSERT INTO `user_roles` VALUES (30, 20, 7, '2026-04-02 18:09:57');
INSERT INTO `user_roles` VALUES (31, 21, 2, '2026-04-02 18:11:36');
INSERT INTO `user_roles` VALUES (32, 22, 2, '2026-04-02 18:12:52');
INSERT INTO `user_roles` VALUES (35, 23, 2, '2026-04-23 09:12:32');
