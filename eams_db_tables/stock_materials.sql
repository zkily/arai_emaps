SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for stock_materials
-- ----------------------------
DROP TABLE IF EXISTS `stock_materials`;
CREATE TABLE `stock_materials`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '库存材料ID',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料名称',
  `manufacture_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '制造编号',
  `quantity` int NOT NULL DEFAULT 0 COMMENT '库存数量',
  `log_date` date NOT NULL COMMENT '日志日期',
  `supplier` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '供应商',
  `material_quality` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '材料质量',
  `is_used` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否已使用(0=未使用,1=已使用)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_material_name`(`material_name` ASC) USING BTREE,
  INDEX `idx_manufacture_no`(`manufacture_no` ASC) USING BTREE,
  INDEX `idx_log_date`(`log_date` ASC) USING BTREE,
  INDEX `idx_supplier`(`supplier` ASC) USING BTREE,
  INDEX `idx_is_used`(`is_used` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4220 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '材料库存管理表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of stock_materials
-- ----------------------------

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
