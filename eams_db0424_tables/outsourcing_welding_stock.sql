SET NAMES utf8mb4;

CREATE TABLE `outsourcing_welding_stock`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `supplier_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `welding_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '溶接種類',
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
  UNIQUE INDEX `uk_product_supplier_welding`(`product_cd` ASC, `supplier_cd` ASC, `welding_type` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_welding_type`(`welding_type` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 226 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注溶接品在庫' ROW_FORMAT = Dynamic;
INSERT INTO `outsourcing_welding_stock` VALUES (22, '92401', '3BV FR', 'OS-005', '溶接', 0, 4604, 0, DEFAULT, 0, 0, '2026-04-23', NULL, '2025-12-12 08:08:50', '2026-04-23 16:43:41');
INSERT INTO `outsourcing_welding_stock` VALUES (33, '91491', 'TKR FR', 'OS-005', '溶接', 4947, 14334, 3780, DEFAULT, 1167, 0, '2026-04-24', NULL, '2025-12-12 08:55:16', '2026-04-24 16:23:00');
INSERT INTO `outsourcing_welding_stock` VALUES (45, '91111', 'TTA', 'OS-005', '溶接', 31860, 81540, 23220, DEFAULT, 8640, 0, '2026-04-24', NULL, '2025-12-12 08:56:30', '2026-04-24 16:23:04');
