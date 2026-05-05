SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for process_routes
-- ----------------------------
DROP TABLE IF EXISTS `process_routes`;
CREATE TABLE `process_routes`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ルートID',
  `route_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'ルートコード',
  `route_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'ルート名称',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '説明',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '使用フラグ',
  `is_default` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'デフォルトフラグ（製品に紐付く場合）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`, `route_cd`) USING BTREE,
  UNIQUE INDEX `route_cd`(`route_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 30 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '工程ルート（ヘッダ）' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of process_routes
-- ----------------------------
INSERT INTO `process_routes` VALUES (1, 'R-STD01', '切面成メ検倉', '切断⇒面取⇒成型⇒メッキ⇒検査⇒倉庫', 1, 1, '2025-05-04 12:08:59', '2025-09-18 16:32:45');
INSERT INTO `process_routes` VALUES (2, 'R-STD02', '切成メ検倉', '切断⇒成型⇒メッキ⇒検査⇒倉庫', 1, 1, '2025-05-04 13:07:48', '2025-09-18 16:32:54');
INSERT INTO `process_routes` VALUES (3, 'R-STD03', '切面成メ溶検倉', '切断⇒面取⇒成型⇒メッキ⇒溶接⇒検査⇒倉庫', 1, 1, '2025-05-04 17:44:52', '2025-09-18 16:33:04');
INSERT INTO `process_routes` VALUES (4, 'R-STD04', '切成メ溶検倉', '切断⇒成型⇒メッキ⇒溶接⇒検査⇒倉庫', 1, 1, '2025-05-07 14:03:30', '2025-09-18 16:33:12');
INSERT INTO `process_routes` VALUES (5, 'R-STD05', '切面成溶メ検倉', '切断⇒面取⇒成型⇒溶接⇒メッキ⇒検査⇒倉庫', 1, 1, '2025-05-07 15:09:33', '2025-09-18 16:33:22');
INSERT INTO `process_routes` VALUES (6, 'R-STD06', '切成溶メ検倉', '切断⇒成型⇒溶接⇒メッキ⇒検査⇒倉庫', 1, 1, '2025-05-07 15:10:25', '2025-09-18 16:33:29');
INSERT INTO `process_routes` VALUES (7, 'R-STD07', '切面成外メ外検前検倉', '切断⇒面取⇒成型⇒外注メッキ⇒外注検査前⇒検査⇒倉庫', 1, 1, '2025-05-07 15:28:23', '2025-10-03 09:02:05');
INSERT INTO `process_routes` VALUES (8, 'R-STD08', '切成外メ外検前検倉', '切断⇒成型⇒外注メッキ⇒外注検査前⇒検査⇒倉庫', 1, 1, '2025-05-07 15:28:38', '2025-10-03 09:02:55');
INSERT INTO `process_routes` VALUES (9, 'R-STD09', '切面成溶外メ外検前検倉', '切断⇒面取⇒成型⇒溶接⇒外注メッキ⇒外注検査前⇒検査⇒倉庫', 1, 1, '2025-05-07 15:31:10', '2025-10-03 09:04:03');
INSERT INTO `process_routes` VALUES (10, 'R-STD10', '切成溶外メ外検前検倉', '切断⇒成型⇒溶接⇒外注メッキ⇒外注検査前⇒検査⇒倉庫', 1, 1, '2025-05-07 15:31:23', '2025-10-03 09:04:58');
INSERT INTO `process_routes` VALUES (11, 'R-STD11', '切面SW成メ検倉', '切断⇒面取⇒成型⇒メッキ⇒検査⇒倉庫', 1, 1, '2025-05-27 09:54:32', '2026-01-16 17:00:57');
INSERT INTO `process_routes` VALUES (12, 'R-STD13', '切面SW成メ溶検倉', '切断⇒面取⇒成型⇒メッキ⇒溶接⇒検査⇒倉庫', 1, 1, '2025-05-27 09:55:30', '2026-01-16 17:01:04');
INSERT INTO `process_routes` VALUES (13, 'R-STD14', '切面SW成溶メ検倉', '切断⇒面取⇒成型⇒溶接⇒メッキ⇒検査⇒倉庫', 1, 1, '2025-05-27 09:56:08', '2026-01-16 17:01:09');
INSERT INTO `process_routes` VALUES (14, 'R-STD15', '切面SW成外メ外検前検倉', '切断⇒面取⇒成型⇒外注メッキ⇒外注検査前⇒検査⇒倉庫', 1, 1, '2025-05-27 09:56:44', '2026-01-16 17:01:14');
INSERT INTO `process_routes` VALUES (15, 'R-STD16', '切面SW成外溶外メ外検前検倉', '切断⇒面取⇒成型⇒外注溶接⇒外注支給前⇒外注メッキ⇒外注検査前⇒検査⇒倉庫', 1, 1, '2025-05-27 09:58:22', '2026-01-16 17:01:20');
INSERT INTO `process_routes` VALUES (16, 'R-STD17', '切面SW成メ前検溶検倉', '切断⇒面取⇒成型⇒メッキ⇒溶接前検査⇒溶接⇒検査⇒倉庫', 1, 1, '2025-05-27 10:13:06', '2026-01-16 17:01:26');
INSERT INTO `process_routes` VALUES (17, 'R-STD18', '切面成外メ外検外倉', '切断⇒面取⇒成型⇒外注メッキ⇒外注倉庫', 1, 1, '2025-05-27 10:57:37', '2025-12-02 08:42:48');
INSERT INTO `process_routes` VALUES (18, 'R-STD19', '切面SW成溶外メ外検前検倉', '切断⇒面取⇒成型⇒溶接⇒外注メッキ⇒外注検査前⇒検査⇒倉庫', 1, 1, '2025-05-27 11:20:05', '2026-01-16 17:01:32');
INSERT INTO `process_routes` VALUES (19, 'R-STD20', '切面SW成外メ外倉', '切断⇒面取⇒成型⇒外注メッキ⇒外注倉庫', 1, 1, '2025-05-27 11:42:36', '2026-01-16 17:01:37');
INSERT INTO `process_routes` VALUES (20, 'R-STD21', '外切倉', '外注切断⇒倉庫', 1, 1, '2025-05-27 11:58:18', '2025-09-18 16:42:57');
INSERT INTO `process_routes` VALUES (21, 'R-STD22', '切成外メ外倉', '切断⇒成型⇒外注メッキ⇒外注倉庫', 1, 1, '2025-05-27 13:34:59', '2025-12-02 08:25:21');
INSERT INTO `process_routes` VALUES (22, 'R-STD23', '切面成検倉', '切断⇒面取⇒成型⇒検査⇒倉庫', 1, 1, '2025-05-27 13:40:56', '2025-09-18 16:43:53');
INSERT INTO `process_routes` VALUES (23, 'R-STD24', '切成検倉', '切断⇒成型⇒検査⇒倉庫', 1, 1, '2025-05-27 13:41:08', '2025-09-18 16:44:16');
INSERT INTO `process_routes` VALUES (24, 'R-STD25', '切成外成検倉', '切断⇒成型⇒外注成型⇒検査⇒倉庫', 1, 1, '2025-05-27 14:14:56', '2025-09-18 16:44:43');
INSERT INTO `process_routes` VALUES (25, 'R-STD26', '切面成外メ外検前溶検倉', '切断⇒面取⇒成型⇒外注メッキ⇒外注検査前⇒溶接⇒検査⇒倉庫', 1, 1, '2025-05-27 14:16:03', '2026-01-06 11:50:24');
INSERT INTO `process_routes` VALUES (26, 'R-STD27', '外切外メ外検前検倉', '切断⇒外注メッキ⇒外注検査前⇒検査⇒倉庫', 1, 1, '2025-05-27 14:20:34', '2025-12-16 16:15:35');
INSERT INTO `process_routes` VALUES (27, 'R-STD12', '外切成メ検倉', '外注切断⇒成型⇒メッキ⇒検査⇒倉庫', 1, 1, '2025-06-02 15:39:07', '2025-09-18 16:46:57');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
