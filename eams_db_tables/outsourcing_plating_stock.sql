SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for outsourcing_plating_stock
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_plating_stock`;
CREATE TABLE `outsourcing_plating_stock`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品名',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先CD',
  `plating_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'メッキ種類',
  `ordered_qty` int NULL DEFAULT 0 COMMENT '発注累計数量',
  `received_qty` int NULL DEFAULT 0 COMMENT '入庫累計数量',
  `used_qty` int NULL DEFAULT 0 COMMENT '出庫累計数量',
  `stock_qty` int GENERATED ALWAYS AS ((`ordered_qty` - `used_qty`)) STORED COMMENT '現在庫数量' NULL,
  `pending_qty` int NULL DEFAULT 0 COMMENT '入庫予定数量',
  `min_stock` int NULL DEFAULT 0 COMMENT '最低在庫数',
  `last_receive_date` date NULL DEFAULT NULL COMMENT '最終入庫日',
  `last_issue_date` date NULL DEFAULT NULL COMMENT '最終出庫日',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_product_supplier`(`product_cd` ASC, `supplier_cd` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 550 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注メッキ品在庫' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of outsourcing_plating_stock
-- ----------------------------
INSERT INTO `outsourcing_plating_stock` VALUES (51, '91811', '3MO CTR', 'OS-001', 'メッキ', 7560, 16567, 6415, DEFAULT, 1145, 0, '2026-04-15', NULL, '2025-12-09 18:38:44', '2026-04-16 11:29:29');
INSERT INTO `outsourcing_plating_stock` VALUES (53, '91831', '3N0 RR EU', 'OS-001', 'メッキ', 12672, 36672, 8958, DEFAULT, 3714, 0, '2026-04-28', NULL, '2025-12-09 18:38:45', '2026-04-28 14:26:12');
INSERT INTO `outsourcing_plating_stock` VALUES (55, '91111', 'TTA', 'OS-001', 'メッキ', 25380, 78840, 18525, DEFAULT, 6855, 0, '2026-04-28', NULL, '2025-12-09 18:38:45', '2026-04-28 14:25:08');
INSERT INTO `outsourcing_plating_stock` VALUES (61, '91491', 'TKR FR', 'OS-001', 'メッキ', 5388, 12599, 5388, DEFAULT, 0, 0, '2026-04-27', NULL, '2025-12-09 18:49:22', '2026-04-28 14:26:00');
INSERT INTO `outsourcing_plating_stock` VALUES (75, '91861', '3V0 FR MASS', 'OS-001', 'メッキ', 1440, 1440, 1440, DEFAULT, 0, 0, '2026-04-15', NULL, '2025-12-10 09:09:30', '2026-04-28 14:26:21');
INSERT INTO `outsourcing_plating_stock` VALUES (103, '92661', 'CH2 RR', 'OS-003', 'メッキ', 31679, 95032, 26878, DEFAULT, 4801, 0, '2026-04-27', NULL, '2025-12-10 09:12:41', '2026-04-29 09:15:23');
INSERT INTO `outsourcing_plating_stock` VALUES (109, '91001', 'HR3 ENCAP', 'OS-002', 'メッキ', 2880, 17186, 0, DEFAULT, 2880, 0, '2026-04-16', NULL, '2025-12-10 09:13:13', '2026-04-16 11:26:45');
INSERT INTO `outsourcing_plating_stock` VALUES (128, '92401', '3BV FR', 'OS-001', 'メッキ', 0, 4064, 0, DEFAULT, 0, 0, '2026-04-27', NULL, '2025-12-10 10:48:51', '2026-04-28 14:27:55');
INSERT INTO `outsourcing_plating_stock` VALUES (151, '91011', 'HR3 JP', 'OS-002', 'メッキ', 5400, 35889, 1860, DEFAULT, 3540, 0, '2026-04-29', NULL, '2025-12-10 11:28:43', '2026-04-27 17:59:36');
INSERT INTO `outsourcing_plating_stock` VALUES (200, '90991', 'FE-7', 'OS-003', 'メッキ', 2200, 384, 2200, DEFAULT, 0, 0, '2026-03-05', NULL, '2025-12-16 10:36:39', '2026-03-17 18:02:55');
INSERT INTO `outsourcing_plating_stock` VALUES (202, '91021', 'IW-187', 'OS-003', 'メッキ', 2000, 0, 2000, DEFAULT, 0, 0, '2025-12-23', NULL, '2025-12-16 10:36:39', '2026-03-17 18:02:57');
INSERT INTO `outsourcing_plating_stock` VALUES (345, '92161', '3V0 FR プレート', 'OS-001', 'メッキ', 7623, 5040, 2980, DEFAULT, 4643, 0, '2026-04-30', NULL, '2026-01-08 16:10:57', '2026-04-27 18:06:35');
INSERT INTO `outsourcing_plating_stock` VALUES (370, '91631', '5A45 FR', 'OS-001', 'メッキ', 0, 3272, 0, DEFAULT, 0, 0, '2026-04-09', NULL, '2026-01-20 10:59:43', '2026-04-23 16:53:17');
INSERT INTO `outsourcing_plating_stock` VALUES (394, '91621', 'RE7 CTR', 'OS-003', 'メッキ', 0, 0, 0, DEFAULT, 0, 0, '2026-01-22', NULL, '2026-01-20 11:02:46', '2026-03-18 10:26:04');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
