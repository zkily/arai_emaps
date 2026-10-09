-- TABLE: carriers
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `carriers` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '運送便ID',
  `carrier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '運送便CD',
  `carrier_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '運送便名称',
  `contact_person` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '連絡人',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '電話番号',
  `shipping_time` time DEFAULT NULL COMMENT '出荷時間',
  `report_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '報告No',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '備考',
  `status` tinyint DEFAULT '1' COMMENT '状態（1=有効, 0=無効）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `carrier_cd` (`carrier_cd`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC COMMENT='運送便マスタ';

SET FOREIGN_KEY_CHECKS = 1;
