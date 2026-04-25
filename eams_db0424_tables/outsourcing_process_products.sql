SET NAMES utf8mb4;

CREATE TABLE `outsourcing_process_products`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_type` enum('cutting','forming','plating','welding','inspection','processing') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程種別（外注切断/外注成型/外注メッキ/外注溶接/外注検査/外注加工）',
  `supplier_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `supplier_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '外注先名',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `specification` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `unit_price` decimal(12, 2) NULL DEFAULT 0.00 COMMENT '単価',
  `delivery_lead_time` int NULL DEFAULT 7 COMMENT '納入リードタイム（日）',
  `delivery_location` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '納入場所',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '区分',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '内容',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_process_supplier_product`(`process_type` ASC, `supplier_cd` ASC, `product_cd` ASC) USING BTREE,
  INDEX `idx_process_type`(`process_type` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_is_active`(`is_active` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 38 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注工程製品マスタ' ROW_FORMAT = DYNAMIC;
INSERT INTO `outsourcing_process_products` VALUES (13, 'plating', 'OS-001', '(有)三和電工', '92401', '3BV FR', NULL, 62.76, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 11:30:58', '2026-04-20 17:21:41', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (14, 'plating', 'OS-001', '(有)三和電工', '91811', '3MO CTR', NULL, 38.46, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 11:53:19', '2026-04-20 17:21:07', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (15, 'plating', 'OS-001', '(有)三和電工', '91111', 'TTA', NULL, 38.46, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:00:30', '2026-04-20 17:20:44', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (16, 'plating', 'OS-001', '(有)三和電工', '91631', '5A45 FR', NULL, 48.59, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:02:06', '2026-04-20 17:20:59', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (17, 'plating', 'OS-001', '(有)三和電工', '92161', '3V0 FR プレート', NULL, 47.57, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:02:31', '2026-04-20 17:21:32', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (18, 'plating', 'OS-001', '(有)三和電工', '91831', '3N0 RR EU', NULL, 46.56, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:03:00', '2026-04-20 17:21:16', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (19, 'plating', 'OS-001', '(有)三和電工', '91491', 'TKR FR', NULL, 38.46, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:03:26', '2026-04-20 17:20:51', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (20, 'plating', 'OS-001', '(有)三和電工', '91861', '3V0 FR MASS', NULL, 87.05, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:04:33', '2026-04-20 17:21:23', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (21, 'plating', 'OS-003', '八洲金属(株)', '90991', 'FE-7', NULL, 15.92, 5, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', '毎週火曜日に出し、来週火曜日受入', 1, '2025-12-04 13:05:03', '2026-04-20 17:22:04', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (22, 'plating', 'OS-003', '八洲金属(株)', '92661', 'CH2 RR', NULL, 28.34, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:05:28', '2026-04-20 17:22:25', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (23, 'plating', 'OS-003', '八洲金属(株)', '91621', 'RE7 CTR', NULL, 28.95, 5, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:06:39', '2026-04-20 17:22:17', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (24, 'plating', 'OS-003', '八洲金属(株)', '91021', 'IW-187', NULL, 20.04, 5, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:07:02', '2026-04-20 17:22:10', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (25, 'plating', 'OS-002', '矢田川電鍍工業(株)', '91011', 'HR3 JP', NULL, 27.84, 2, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:07:50', '2026-04-20 17:21:55', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (26, 'plating', 'OS-002', '矢田川電鍍工業(株)', '91001', 'HR3 ENCAP', NULL, 27.84, 2, '仕上倉庫ヤード下', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:08:13', '2026-04-20 17:21:49', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (27, 'plating', 'OS-004', '北九州ケミカル', '92221', '900B FR', NULL, 49.12, 4, 'その他', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:09:08', '2026-04-20 17:22:42', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (28, 'plating', 'OS-004', '北九州ケミカル', '92231', '900B RR', NULL, 40.62, 4, 'その他', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:09:50', '2026-04-20 17:22:49', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (29, 'plating', 'OS-004', '北九州ケミカル', '92091', '900B 対米', NULL, 43.53, 4, 'その他', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2025-12-04 13:10:24', '2026-04-20 17:22:35', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (30, 'forming', 'OS-006', '立松プレス工業(資)', '92521', 'X11M FR1', NULL, 12.15, 3, '仕上倉庫ヤード下', 'ステー無償支給', 'ステー加工', NULL, 1, '2025-12-04 13:18:35', '2026-04-20 17:20:34', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (31, 'welding', 'OS-005', '共栄工業(株)', '91111', 'TTA', NULL, 24.75, 3, '引き取り', 'ステー無償支給', 'ブラケット溶接', NULL, 1, '2025-12-04 13:21:52', '2025-12-11 16:07:56', NULL, NULL);
INSERT INTO `outsourcing_process_products` VALUES (32, 'welding', 'OS-005', '共栄工業(株)', '91491', 'TKR FR', NULL, 24.82, 3, '引き取り', 'ステー無償支給', 'ブラケット溶接', NULL, 1, '2025-12-04 13:22:14', '2025-12-11 16:08:01', NULL, NULL);
INSERT INTO `outsourcing_process_products` VALUES (33, 'welding', 'OS-005', '共栄工業(株)', '92401', '3BV FR', NULL, 25.16, 3, '引き取り', 'ステー無償支給', 'ブラケット溶接', NULL, 1, '2025-12-04 13:22:35', '2025-12-11 16:08:06', NULL, NULL);
INSERT INTO `outsourcing_process_products` VALUES (34, 'plating', 'OS-004', '北九州ケミカル', '92781', '410D CTR', NULL, 48.13, 4, 'その他', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2026-01-09 16:47:09', '2026-04-20 17:23:22', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (35, 'plating', 'OS-004', '北九州ケミカル', '92751', '410D FR1', NULL, 56.68, 4, 'その他', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2026-01-23 13:03:13', '2026-04-20 17:23:13', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (36, 'plating', 'OS-004', '北九州ケミカル', '92541', '410D FR2', NULL, 49.12, 4, 'その他', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2026-01-23 13:04:16', '2026-04-20 17:23:06', NULL, 'zkily');
INSERT INTO `outsourcing_process_products` VALUES (37, 'plating', 'OS-004', '北九州ケミカル', '92431', '410D RR', NULL, 43.30, 4, 'その他', 'ステー無償支給', 'メッキ塗装', NULL, 1, '2026-01-23 13:06:06', '2026-04-20 17:22:59', NULL, 'zkily');
