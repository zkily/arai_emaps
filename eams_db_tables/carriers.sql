SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for carriers
-- ----------------------------
DROP TABLE IF EXISTS `carriers`;
CREATE TABLE `carriers`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '運送便ID',
  `carrier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '運送便CD',
  `carrier_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '運送便名称',
  `contact_person` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '連絡人',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '電話番号',
  `shipping_time` time NULL DEFAULT NULL COMMENT '出荷時間',
  `report_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '報告No',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '備考',
  `status` tinyint NULL DEFAULT 1 COMMENT '状態（1=有効, 0=無効）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `carrier_cd`(`carrier_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '運送便マスタ' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of carriers
-- ----------------------------
INSERT INTO `carriers` VALUES (1, 'U01', '社内便2T', '営業部', '', '12:00:00', '2', '2ドントラック', 1, '2025-04-24 16:38:57', '2025-05-29 09:57:40');
INSERT INTO `carriers` VALUES (3, 'U03', 'TG便', '', '', '09:30:00', '3', '', 0, '2025-04-24 18:52:39', '2025-05-16 09:32:15');
INSERT INTO `carriers` VALUES (4, 'U02', '鈴鹿便', '', '', '09:30:00', '3', '4ドントラック', 1, '2025-04-24 18:53:20', '2025-06-16 08:22:41');
INSERT INTO `carriers` VALUES (5, 'U06', '佐川急便', '', '', '15:00:00', '1', '', 1, '2025-04-25 11:39:34', '2025-05-29 09:55:39');
INSERT INTO `carriers` VALUES (6, 'U07', 'ヤマト運輸', '', '', '15:00:00', '1', '', 1, '2025-04-25 11:39:56', '2025-04-25 11:52:37');
INSERT INTO `carriers` VALUES (7, 'U10', 'オワリ運送午後', '', '', '14:00:00', '1', '10ドントラック', 1, '2025-04-25 11:40:24', '2025-06-16 08:23:37');
INSERT INTO `carriers` VALUES (8, 'U11', '社内午後便', '木村', '', '15:00:00', '2', '10ドントラック', 1, '2025-04-25 11:40:58', '2025-05-29 09:57:58');
INSERT INTO `carriers` VALUES (9, 'U13', 'JPロジスティクス', '', '', '15:00:00', '1', '', 1, '2025-04-25 11:41:17', '2025-05-13 16:11:01');
INSERT INTO `carriers` VALUES (12, 'U04', 'コンテナ便', '', '', '10:00:57', '4', '輸出用コンテナ', 1, '2025-05-29 09:56:33', '2025-05-29 09:57:16');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
