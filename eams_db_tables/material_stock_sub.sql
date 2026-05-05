SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for material_stock_sub
-- ----------------------------
DROP TABLE IF EXISTS `material_stock_sub`;
CREATE TABLE `material_stock_sub`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料CD',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料名',
  `date` date NOT NULL COMMENT '日期',
  `current_stock` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '现在在庫',
  `safety_stock` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '安全在庫',
  `max_stock` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '最大在庫',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '単位',
  `unit_price` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '単価',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '仕入先CD',
  `supplier_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '仕入先名',
  `lead_time` int NULL DEFAULT 0 COMMENT 'リードタイム',
  `planned_usage` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '計画使用数',
  `order_quantity` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '注文束数',
  `order_bundle_quantity` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '注文本数',
  `bundle_weight` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '捆重量',
  `order_amount` decimal(15, 2) NULL DEFAULT 0.00 COMMENT '注文金額',
  `standard_spec` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `pieces_per_bundle` int NULL DEFAULT 0 COMMENT '每捆件数',
  `long_weight` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '长重量',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `label_color` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ラベル色（白/緑）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最終更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_material_cd_date`(`material_cd` ASC, `date` ASC) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 51 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '材料在庫子表（手动注文数据）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of material_stock_sub
-- ----------------------------
INSERT INTO `material_stock_sub` VALUES (30, '10128', '12.0×2.30×5621', '2026-03-02', 1.00, 0.00, 0.00, '本', 0.00, '103', '丸一INOAC', 0, 0.00, 1.00, 158.00, 0.00, 0.00, NULL, 326, 0.00, 'バラ束158本、試作用', '白', '2026-03-24 13:23:15', '2026-04-02 11:14:26');
INSERT INTO `material_stock_sub` VALUES (44, '10028', '14.0×1.35×5290', '2026-04-24', 0.00, 4.00, 0.00, '本', 213.30, '101', '岡島NST', 5, 1.00, 1.00, 186.00, 414.41, 88393.23, 'H800C', 300, 2.23, 'バラ束', NULL, '2026-04-24 09:12:41', '2026-04-28 09:31:56');
INSERT INTO `material_stock_sub` VALUES (45, '10028', '14.0×1.35×5290', '2026-04-24', 0.00, 4.00, 0.00, '本', 213.30, '101', '岡島NST', 5, 1.00, 1.00, 95.00, 211.66, 45147.08, 'H800C', 300, 2.23, 'バラ束', NULL, '2026-04-24 09:13:48', '2026-04-28 09:31:54');
INSERT INTO `material_stock_sub` VALUES (46, '10084', '12.7×2.00×4160', '2026-04-24', 1.00, 1.00, 0.00, '本', 196.00, '104', '丸一ﾒﾀﾙｱｸﾄ', 10, 0.00, 1.00, 260.00, 570.70, 111857.20, 'STKM13A', 500, 2.20, 'バラ束', NULL, '2026-04-24 09:14:27', '2026-04-24 09:14:27');
INSERT INTO `material_stock_sub` VALUES (47, '10060', '14.0×2.30×4929', '2026-04-28', 0.00, 2.00, 0.00, '本', 233.30, '104', '丸一ﾒﾀﾙｱｸﾄ', 2, 1.00, 1.00, 123.00, 402.33, 93864.29, 'INOAC74', 326, 3.27, 'バラ束123本', NULL, '2026-04-27 09:59:14', '2026-04-28 09:32:00');
INSERT INTO `material_stock_sub` VALUES (48, '10015', '12.0×1.35×4300', '2026-05-07', 1.00, 1.00, 0.00, '本', 232.30, '101', '岡島NST', 5, 0.00, 1.00, 342.00, 521.55, 121156.07, 'H800C', 500, 1.53, 'バラ束', NULL, '2026-04-28 13:38:35', '2026-04-28 13:38:35');
INSERT INTO `material_stock_sub` VALUES (49, '10087', '14.0×2.30×4730', '2026-05-08', 1.00, 2.00, 0.00, '本', 218.20, '105', 'JFE溶接鋼管(株)', 5, 0.00, 1.00, 157.00, 492.82, 107533.98, 'INOAC55', 250, 3.14, 'バラ束', NULL, '2026-04-28 13:39:35', '2026-04-28 13:39:35');
INSERT INTO `material_stock_sub` VALUES (50, '10087', '14.0×2.30×4730', '2026-05-08', 1.00, 2.00, 0.00, '本', 218.20, '105', 'JFE溶接鋼管(株)', 5, 0.00, 1.00, 93.00, 291.93, 63698.47, 'INOAC55', 250, 3.14, 'バラ束', NULL, '2026-04-28 13:39:52', '2026-04-28 13:39:52');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
