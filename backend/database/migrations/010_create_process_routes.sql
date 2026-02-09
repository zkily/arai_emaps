SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for process_routes (工程ルートヘッダ)
-- ----------------------------
DROP TABLE IF EXISTS `process_routes`;
CREATE TABLE `process_routes` (
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
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工程ルート（ヘッダ）' ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for process_route_steps (ルートステップ)
-- ----------------------------
DROP TABLE IF EXISTS `process_route_steps`;
CREATE TABLE `process_route_steps` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ルートステップID',
  `route_cd` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートID',
  `step_no` int NOT NULL COMMENT 'ステップ番号',
  `process_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '工程ID',
  `yield_percent` decimal(5, 2) NULL DEFAULT 100.00 COMMENT '歩留率（%）',
  `cycle_sec` decimal(5, 2) NULL DEFAULT 0.00 COMMENT '標準サイクル（秒）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
