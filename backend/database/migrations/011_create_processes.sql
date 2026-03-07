SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for processes (工程マスタ)
-- ----------------------------
DROP TABLE IF EXISTS `processes`;
CREATE TABLE `processes` (
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
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '工程マスタ' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
