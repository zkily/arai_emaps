SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for customers
-- ----------------------------
DROP TABLE IF EXISTS `customers`;
CREATE TABLE `customers`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '顧客ID',
  `customer_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '顧客CD',
  `customer_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '顧客名',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '電話番号',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '住所',
  `customer_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '顧客種別（corporate, individual, agency 等）',
  `status` tinyint NULL DEFAULT 1 COMMENT '状態（1=有効, 0=無効）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `customer_cd`(`customer_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 16 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '顧客マスタ' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of customers
-- ----------------------------
INSERT INTO `customers` VALUES (1, 'C01', '(株)イノアックコーポレーション', '052-581-1098', '愛知県名古屋市中村区名駅南二丁目13番4号', '法人', 1, '2025-04-24 16:34:44', '2025-05-11 20:11:03');
INSERT INTO `customers` VALUES (4, 'C02', '(株)東海化成', '', '', '法人', 1, '2025-04-25 11:37:04', '2025-05-11 20:11:00');
INSERT INTO `customers` VALUES (5, 'C03', '(株)タチエス', '', '', '法人', 1, '2025-04-25 11:37:18', '2025-05-11 20:10:55');
INSERT INTO `customers` VALUES (6, 'C04', 'メタルアクト(株)', '', '', '法人', 1, '2025-04-25 11:37:30', '2025-05-11 20:09:59');
INSERT INTO `customers` VALUES (7, 'C05', '日本発条(株)', '', '', '法人', 1, '2025-04-25 11:37:41', '2025-05-11 20:09:55');
INSERT INTO `customers` VALUES (8, 'C06', '双葉産業(株)', '', '', '法人', 1, '2025-04-25 11:37:51', '2025-05-11 20:09:52');
INSERT INTO `customers` VALUES (9, 'C07', '(株)豊和化成', '', '', '法人', 1, '2025-04-25 11:38:01', '2025-05-11 20:09:48');
INSERT INTO `customers` VALUES (10, 'C08', 'アディエント', '', '', '法人', 1, '2025-04-25 11:38:11', '2025-05-11 20:09:45');
INSERT INTO `customers` VALUES (11, 'C09', '錦陵工業(株)', '', '', '法人', 1, '2025-04-25 11:38:20', '2025-05-12 17:24:47');
INSERT INTO `customers` VALUES (12, 'C10', 'IICトレーディア', '', '', '法人', 1, '2025-04-25 11:38:30', '2025-05-11 20:09:37');
INSERT INTO `customers` VALUES (13, 'C99', 'その他', '', '', '法人', 1, '2025-04-25 11:38:53', '2025-05-16 09:26:11');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
