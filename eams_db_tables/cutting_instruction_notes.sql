SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for cutting_instruction_notes
-- ----------------------------
DROP TABLE IF EXISTS `cutting_instruction_notes`;
CREATE TABLE `cutting_instruction_notes`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `scope` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'cutting_instruction',
  `content` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_done` tinyint NOT NULL DEFAULT 0 COMMENT '0:未完了 1:完了',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_scope_is_done_created_at`(`scope` ASC, `is_done` ASC, `created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of cutting_instruction_notes
-- ----------------------------
INSERT INTO `cutting_instruction_notes` VALUES (1, 'cutting_instruction', '030A SIDE と826料金トレー取り合わせ', 0, 'zkily', '2026-04-29 16:47:23', '2026-04-29 16:47:23');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
