SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for destinations
-- ----------------------------
DROP TABLE IF EXISTS `destinations`;
CREATE TABLE `destinations`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '納入先ID',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先名称',
  `customer_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '顧客CD（外部キー）',
  `carrier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '運送会社CD（外部キー）',
  `delivery_lead_time` int NULL DEFAULT 0 COMMENT '納入リードタイム（日）',
  `issue_type` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '自動' COMMENT '発行区分',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '電話番号',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '住所',
  `status` tinyint NULL DEFAULT 1 COMMENT '状态（1=启用, 0=停用）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日',
  `picked_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `destination_cd`(`destination_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 123 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '納入先マスタ' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of destinations
-- ----------------------------
INSERT INTO `destinations` VALUES (80, 'N00', '未定', 'C11', 'U13', 2, '1', NULL, NULL, 0, '2025-04-25 11:44:55', '2025-07-04 08:10:33', NULL);
INSERT INTO `destinations` VALUES (81, 'N03', '(株)九州INOAC北九州', 'C01', 'U10', 3, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:16:22', NULL);
INSERT INTO `destinations` VALUES (82, 'N05', '(株)東北INOAC小牛田', 'C01', 'U10', 3, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:16:24', NULL);
INSERT INTO `destinations` VALUES (83, 'N06', '(株)九州INOAC浮羽', 'C01', 'U10', 3, '1', NULL, NULL, 0, '2025-04-25 11:44:55', '2025-07-04 08:10:38', NULL);
INSERT INTO `destinations` VALUES (84, 'N08', '共栄工業(株)', 'C01', 'U11', 1, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:16:43', NULL);
INSERT INTO `destinations` VALUES (85, 'N10', '(株)西浦化学', 'C01', 'U10', 1, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:16:45', NULL);
INSERT INTO `destinations` VALUES (86, 'N11', '(株)富士精機', 'C09', 'U10', 1, '2', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-29 10:15:29', NULL);
INSERT INTO `destinations` VALUES (87, 'N12', '(株)タチエス愛知', 'C03', 'U11', 1, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:16:54', NULL);
INSERT INTO `destinations` VALUES (88, 'N13', '(株)タチエス武蔵', 'C03', 'U11', 2, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:16:59', NULL);
INSERT INTO `destinations` VALUES (89, 'N14', '(株)タチエス鈴鹿', 'C03', 'U02', 0, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:04', NULL);
INSERT INTO `destinations` VALUES (90, 'N15', '(株)タチエス平塚', 'C03', 'U11', 2, '3', NULL, NULL, 0, '2025-04-25 11:44:55', '2025-05-29 09:52:43', NULL);
INSERT INTO `destinations` VALUES (91, 'N17', 'タカヤ化成(株)', 'C09', 'U11', 3, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:10', NULL);
INSERT INTO `destinations` VALUES (92, 'N18', '(株)東海化成', 'C02', 'U11', 2, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:12', NULL);
INSERT INTO `destinations` VALUES (93, 'N20', '東名化成(株)', 'C05', 'U11', 3, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:14', NULL);
INSERT INTO `destinations` VALUES (94, 'N21', '日本発条群馬工場', 'C05', 'U11', 3, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:16', NULL);
INSERT INTO `destinations` VALUES (95, 'N22', '秋田工業(株)', 'C01', 'U11', 1, '3', NULL, NULL, 0, '2025-04-25 11:44:55', '2025-05-29 09:52:36', NULL);
INSERT INTO `destinations` VALUES (96, 'N24', '(株)豊和化成', 'C01', 'U11', 2, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:20', NULL);
INSERT INTO `destinations` VALUES (97, 'N26', '(株)古口工業', 'C11', 'U06', 2, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-07-04 08:09:37', NULL);
INSERT INTO `destinations` VALUES (98, 'N28', '(株)INOAC南濃', 'C01', 'U11', 1, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:26', NULL);
INSERT INTO `destinations` VALUES (99, 'N29', '(株)ニフコ', 'C01', 'U06', 1, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-06-26 13:55:19', NULL);
INSERT INTO `destinations` VALUES (100, 'N30', '松本工業群馬工場', 'C05', 'U11', 3, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:30', NULL);
INSERT INTO `destinations` VALUES (102, 'N33', 'IICトレーディア', 'C01', 'U13', 1, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:38', NULL);
INSERT INTO `destinations` VALUES (103, 'N34', '(株)東洋グリーンライト', 'C05', 'U10', 2, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:40', NULL);
INSERT INTO `destinations` VALUES (104, 'N36', '(株)シンテック', 'C06', 'U11', 1, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:42', NULL);
INSERT INTO `destinations` VALUES (105, 'N37', '(株)加地', 'C01', 'U13', 2, '1', NULL, NULL, 0, '2025-04-25 11:44:55', '2025-05-29 09:52:15', NULL);
INSERT INTO `destinations` VALUES (106, 'N38', '(株)INOAC吉良', 'C01', 'U10', 1, '2', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:47', NULL);
INSERT INTO `destinations` VALUES (107, 'N39', '日本発条横浜工場', 'C05', 'U11', 2, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:49', NULL);
INSERT INTO `destinations` VALUES (108, 'N42', 'キムラユニティー(株)', 'C01', 'U11', 1, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:51', NULL);
INSERT INTO `destinations` VALUES (109, 'N43', '豊通物流三好センター', 'C05', 'U01', 1, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-07-17 09:53:56', NULL);
INSERT INTO `destinations` VALUES (110, 'N44', '石島運輸倉庫', 'C05', 'U11', 3, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:55', NULL);
INSERT INTO `destinations` VALUES (111, 'N48', 'アディエント追浜', 'C08', 'U11', 3, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:57', NULL);
INSERT INTO `destinations` VALUES (112, 'N50', '(株)東海化成九州', 'C02', 'U11', 3, '3', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:17:58', NULL);
INSERT INTO `destinations` VALUES (113, 'N51', '双葉産業(株)', 'C06', 'U09', 0, '1', NULL, NULL, 0, '2025-04-25 11:44:55', '2025-05-29 09:52:09', NULL);
INSERT INTO `destinations` VALUES (114, 'N52', '(株)佐野工業', 'C01', 'U11', 1, '3', NULL, NULL, 0, '2025-04-25 11:44:55', '2025-07-04 08:09:25', NULL);
INSERT INTO `destinations` VALUES (115, 'N55', '九州ケミカル', 'C01', 'U10', 3, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-05-11 20:18:07', NULL);
INSERT INTO `destinations` VALUES (116, 'N56', '北九州ケミカル', 'C01', 'U15', 0, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-06-25 17:54:50', NULL);
INSERT INTO `destinations` VALUES (117, 'N57', 'メキシコ輸出', 'C01', 'U04', 0, '1', NULL, NULL, 1, '2025-04-25 11:44:55', '2025-09-23 14:53:49', NULL);
INSERT INTO `destinations` VALUES (118, 'N99', 'その他', 'C11', 'U09', 1, '1', NULL, NULL, 0, '2025-04-25 11:44:55', '2025-07-04 08:09:15', NULL);
INSERT INTO `destinations` VALUES (120, 'N58', '東武物流サービス㈱ 新田第二事業所', 'C05', 'U11', 3, '3', '', '', 0, '2025-09-23 14:53:43', '2025-12-05 09:41:53', NULL);
INSERT INTO `destinations` VALUES (121, 'N59', '鈴与(株) 鈴鹿物流センター', 'C05', 'U02', 0, '1', '', '', 1, '2025-10-16 11:39:57', '2026-03-26 17:49:26', NULL);
INSERT INTO `destinations` VALUES (122, 'N60', '(株)星川産業群馬営業所', 'C05', 'U11', 3, '3', NULL, NULL, 1, '2026-04-23 10:20:18', '2026-04-23 11:39:18', NULL);

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
