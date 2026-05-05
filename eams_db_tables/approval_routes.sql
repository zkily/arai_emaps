SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for approval_routes
-- ----------------------------
DROP TABLE IF EXISTS `approval_routes`;
CREATE TABLE `approval_routes`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ルート名',
  `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '種類（amount:金額, department:部門, custom:カスタム）',
  `condition_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '条件タイプ',
  `condition_value` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '条件値（例: 10万円未満, 営業部）',
  `condition_min` decimal(15, 2) NULL DEFAULT NULL COMMENT '金額条件（最小）',
  `condition_max` decimal(15, 2) NULL DEFAULT NULL COMMENT '金額条件（最大）',
  `condition_department_id` int NULL DEFAULT NULL COMMENT '部門条件',
  `priority` int NULL DEFAULT 0 COMMENT '優先度（同条件時の判定順序）',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_approval_routes_type`(`type` ASC) USING BTREE,
  INDEX `idx_approval_routes_active`(`is_active` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '承認ルートテーブル' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of approval_routes
-- ----------------------------
INSERT INTO `approval_routes` VALUES (1, '通常購買承認', 'amount', NULL, '10万円未満', NULL, 100000.00, NULL, 1, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `approval_routes` VALUES (2, '高額購買承認', 'amount', NULL, '10万円以上100万円未満', 100000.00, 1000000.00, NULL, 2, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');
INSERT INTO `approval_routes` VALUES (3, '大規模購買承認', 'amount', NULL, '100万円以上', 1000000.00, NULL, NULL, 3, 1, '2026-02-05 18:08:14', '2026-02-05 18:08:14');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
