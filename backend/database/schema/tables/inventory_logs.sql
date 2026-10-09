-- TABLE: inventory_logs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inventory_logs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '棚卸ログID',
  `item` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '項目（材料棚卸/部品棚卸/製品棚卸）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品/材料/部品CD',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品/材料/部品名',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '工程CD',
  `log_date` date NOT NULL COMMENT '日付',
  `log_time` time NOT NULL COMMENT '時間',
  `hd_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT 'HDNo',
  `pack_qty` int DEFAULT NULL COMMENT '入数（箱/パック単位）',
  `case_qty` int DEFAULT NULL COMMENT 'ケース数',
  `quantity` int NOT NULL COMMENT '数量',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '担当者CDなど',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_log_date` (`log_date`) USING BTREE,
  KEY `idx_process_date` (`process_cd`,`log_date`) USING BTREE,
  KEY `idx_item_date_time` (`item`,`log_date`,`log_time`) USING BTREE,
  KEY `idx_dup_key` (`item`,`product_cd`,`product_name`,`log_date`,`log_time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC COMMENT='棚卸ログ';

SET FOREIGN_KEY_CHECKS = 1;
