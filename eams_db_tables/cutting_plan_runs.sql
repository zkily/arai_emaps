SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for cutting_plan_runs
-- ----------------------------
DROP TABLE IF EXISTS `cutting_plan_runs`;
CREATE TABLE `cutting_plan_runs`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `production_month` date NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'DRAFT',
  `generated_at` datetime NULL DEFAULT NULL,
  `published_at` datetime NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_cutting_plan_runs_month`(`production_month` ASC) USING BTREE,
  INDEX `idx_cutting_plan_runs_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '切断計画Run' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of cutting_plan_runs
-- ----------------------------

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
