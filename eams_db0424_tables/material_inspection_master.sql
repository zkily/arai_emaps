SET NAMES utf8mb4;

CREATE TABLE `material_inspection_master`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `inspection_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '检验代码',
  `inspection_standard` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '检验标准',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_inspection_cd`(`inspection_cd` ASC) USING BTREE COMMENT '检验代码唯一索引'
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '材料检验标准主表' ROW_FORMAT = Dynamic;
INSERT INTO `material_inspection_master` VALUES (1, '403', '14.0×1.00×', '2025-09-25 09:39:01', '2025-09-25 09:39:01');
INSERT INTO `material_inspection_master` VALUES (2, '836', '14.0×2.30×', '2025-09-25 09:39:24', '2025-09-25 09:39:24');
INSERT INTO `material_inspection_master` VALUES (3, '494', '12.0×1.35×', '2025-09-25 09:39:33', '2025-09-25 09:39:33');
INSERT INTO `material_inspection_master` VALUES (4, '658', '14.0×1.35×', '2025-09-25 09:39:41', '2025-09-25 09:39:41');
INSERT INTO `material_inspection_master` VALUES (5, '458', '12.0×1.50×', '2025-09-25 09:39:49', '2025-09-25 09:39:49');
INSERT INTO `material_inspection_master` VALUES (6, '631', '12.0×2.30×', '2025-09-25 09:39:56', '2025-09-25 09:39:56');
INSERT INTO `material_inspection_master` VALUES (7, '312', '12.0×1.40×', '2025-09-25 09:40:03', '2025-09-25 09:40:03');
INSERT INTO `material_inspection_master` VALUES (8, '621', '10.0×2.00×', '2025-09-25 09:40:10', '2025-09-25 09:40:10');
INSERT INTO `material_inspection_master` VALUES (9, '130', '12.7×1.60×', '2025-09-25 09:40:17', '2025-09-25 09:40:17');
INSERT INTO `material_inspection_master` VALUES (10, '132', '12.7×2.00×', '2025-09-25 09:40:24', '2025-09-25 09:40:24');
INSERT INTO `material_inspection_master` VALUES (11, '228', '14.0×2.00×', '2025-09-25 09:40:31', '2025-09-25 09:40:31');
INSERT INTO `material_inspection_master` VALUES (12, '128', '12.7×1.40×', '2025-09-25 09:40:38', '2025-09-25 09:40:38');
