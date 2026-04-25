SET NAMES utf8mb4;

CREATE TABLE `processes`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '工程ID',
  `process_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '工程コード',
  `process_name` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '工程名称',
  `short_name` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '略称／2〜3文字表示用',
  `category` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `is_outsource` tinyint(1) NOT NULL DEFAULT 0 COMMENT '外注フラグ(1=外注)',
  `default_cycle_sec` float NOT NULL DEFAULT 0 COMMENT '標準サイクルタイム(秒)',
  `default_yield` decimal(5, 3) NOT NULL DEFAULT 1.000 COMMENT '歩留(0〜1)',
  `capacity_unit` enum('pcs','kg','m') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'pcs' COMMENT '能力単位',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '備考',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `process_cd`(`process_cd` ASC) USING BTREE,
  INDEX `idx_category`(`category` ASC) USING BTREE,
  INDEX `idx_outsource`(`is_outsource` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 21 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '工程マスタ' ROW_FORMAT = DYNAMIC;
INSERT INTO `processes` VALUES (1, 'KT01', '切断', '切', 'cut', 0, 8.3, 0.999, 'pcs', NULL, '2025-05-04 10:53:52', '2025-05-13 16:19:58');
INSERT INTO `processes` VALUES (2, 'KT02', '面取', '面', 'chamfer', 0, 11.8, 0.999, 'pcs', NULL, '2025-05-04 10:59:25', '2025-05-07 17:08:41');
INSERT INTO `processes` VALUES (3, 'KT03', 'SW', 'SW', 'swaging', 0, 11.8, 0.999, 'pcs', NULL, '2025-05-04 11:04:13', '2025-05-07 17:08:53');
INSERT INTO `processes` VALUES (4, 'KT04', '成型', '成', 'forming', 0, 29.5, 0.998, 'pcs', NULL, '2025-05-04 11:05:05', '2025-05-07 17:09:03');
INSERT INTO `processes` VALUES (5, 'KT05', 'メッキ', 'メ', 'plating', 0, 2.3, 0.998, 'pcs', NULL, '2025-05-04 11:05:46', '2025-05-07 17:09:09');
INSERT INTO `processes` VALUES (6, 'KT06', '外注メッキ', '外メ', 'plating', 1, 2.3, 0.998, 'pcs', NULL, '2025-05-04 11:06:19', '2025-05-07 17:09:14');
INSERT INTO `processes` VALUES (7, 'KT07', '溶接', '溶', 'weld', 0, 27.7, 0.999, 'pcs', NULL, '2025-05-04 11:07:05', '2025-05-07 17:09:19');
INSERT INTO `processes` VALUES (8, 'KT08', '外注溶接', '外溶', 'weld', 1, 27.7, 0.999, 'pcs', NULL, '2025-05-04 11:07:23', '2025-05-07 17:09:25');
INSERT INTO `processes` VALUES (9, 'KT09', '検査', '検', 'inspect', 0, 7.6, 0.993, 'pcs', NULL, '2025-05-04 11:07:58', '2025-05-07 17:09:38');
INSERT INTO `processes` VALUES (10, 'KT10', '外注検査', '外検', 'inspect', 1, 7.6, 0.995, 'pcs', NULL, '2025-05-04 11:08:15', '2025-05-07 17:09:47');
INSERT INTO `processes` VALUES (11, 'KT11', '溶接前検査', '溶前検', 'inspect', 0, 7.6, 0.997, 'pcs', NULL, '2025-05-07 13:53:23', '2025-05-07 17:09:55');
INSERT INTO `processes` VALUES (12, 'KT12', '外注成型', '外成', 'forming', 1, 29.5, 0.999, 'pcs', NULL, '2025-05-07 13:54:51', '2025-05-07 17:10:06');
INSERT INTO `processes` VALUES (13, 'KT13', '倉庫', '倉', 'warehouse', 0, 1, 1.000, 'pcs', NULL, '2025-05-09 14:24:00', '2025-06-03 18:22:33');
INSERT INTO `processes` VALUES (14, 'KT14', '外注切断', '外切', 'cut', 1, 1, 1.000, 'pcs', NULL, '2025-05-27 11:59:04', '2025-05-27 14:30:18');
INSERT INTO `processes` VALUES (15, 'KT15', '外注倉庫', '外倉', 'warehouse', 1, 1, 1.000, 'pcs', NULL, '2025-06-03 18:23:17', '2025-06-03 18:23:17');
INSERT INTO `processes` VALUES (16, 'KT16', '外注支給前', '外支', 'warehouse', 0, 1, 1.000, 'pcs', NULL, '2025-06-03 18:24:16', '2025-10-01 15:49:58');
INSERT INTO `processes` VALUES (17, 'KT17', '外注検査前', '外未検', 'warehouse', 0, 1, 1.000, 'pcs', NULL, '2025-06-03 18:24:41', '2025-10-01 15:49:46');
INSERT INTO `processes` VALUES (18, 'KT18', '部品', '部', 'warehouse', 0, 1, 1.000, 'pcs', NULL, '2025-06-28 16:08:05', '2025-06-28 16:08:05');
INSERT INTO `processes` VALUES (19, 'KT19', '材料', '材', 'warehouse', 0, 1, 1.000, 'pcs', NULL, '2025-06-28 16:08:19', '2025-06-28 16:08:19');
INSERT INTO `processes` VALUES (20, 'KT20', '外注溶接前', '外溶前', 'plating', 1, 1, 1.000, 'pcs', NULL, '2025-10-03 09:12:26', '2025-10-03 09:12:26');
