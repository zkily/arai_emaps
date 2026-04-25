SET NAMES utf8mb4;

CREATE TABLE `outsourcing_suppliers`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '外注先ID',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `supplier_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先名',
  `supplier_type` enum('plating','welding','cutting','forming','parts_processing') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'plating' COMMENT '外注種別（メッキ/溶接/切断/成型/部品加工）',
  `postal_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '郵便番号',
  `address` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '住所',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '電話番号',
  `fax` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'FAX番号',
  `contact_person` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '担当者名',
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'メールアドレス',
  `payment_terms` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '支払条件',
  `lead_time_days` int NULL DEFAULT 7 COMMENT '標準リードタイム（日）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_supplier_type`(`supplier_type` ASC) USING BTREE,
  INDEX `idx_is_active`(`is_active` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 24 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注先マスタ' ROW_FORMAT = Dynamic;
INSERT INTO `outsourcing_suppliers` VALUES (9, 'OS-001', '(有)三和電工', 'plating', NULL, '', '', '', '', '', '', 3, '', 1, '2025-12-04 09:47:05', '2026-03-17 09:07:21');
INSERT INTO `outsourcing_suppliers` VALUES (10, 'OS-002', '矢田川電鍍工業(株)', 'plating', NULL, '', '', '', '', '', '', 3, '', 1, '2025-12-04 09:53:24', '2025-12-08 14:25:44');
INSERT INTO `outsourcing_suppliers` VALUES (11, 'OS-003', '八洲金属(株)', 'plating', NULL, '', '', '', '', '', '', 2, '', 1, '2025-12-04 09:53:49', '2026-03-17 17:08:12');
INSERT INTO `outsourcing_suppliers` VALUES (12, 'OS-004', '北九州ケミカル', 'plating', NULL, '', '', '', '', '', '', 4, '', 1, '2025-12-04 09:55:23', '2026-03-19 16:19:56');
INSERT INTO `outsourcing_suppliers` VALUES (13, 'OS-005', '共栄工業(株)', 'welding', NULL, '', '', '', '', '', '', 3, '', 1, '2025-12-04 13:11:22', '2026-03-17 09:06:30');
INSERT INTO `outsourcing_suppliers` VALUES (14, 'OS-006', '立松プレス工業(資)', 'forming', NULL, '', '', '', '', '', '', 5, '', 1, '2025-12-04 13:11:49', '2025-12-08 14:25:44');
