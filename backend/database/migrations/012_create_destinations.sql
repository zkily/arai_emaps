SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for destinations (納入先マスタ)
-- ----------------------------
DROP TABLE IF EXISTS `destinations`;
CREATE TABLE `destinations` (
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
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '納入先マスタ' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for destination_holidays (納入先の休日設定)
-- ----------------------------
DROP TABLE IF EXISTS `destination_holidays`;
CREATE TABLE `destination_holidays` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `holiday_date` date NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_dest_date`(`destination_cd` ASC, `holiday_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '納入先の休日設定' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for destination_workdays (納入先臨時出勤日)
-- ----------------------------
DROP TABLE IF EXISTS `destination_workdays`;
CREATE TABLE `destination_workdays` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先マスタCD',
  `work_date` date NOT NULL COMMENT '土日の出勤日',
  `reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '理由',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_work_day`(`destination_cd` ASC, `work_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '納入先臨時出勤日マスタ（休日例外）' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
