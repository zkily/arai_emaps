-- TABLE: order_monthly
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `order_monthly` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '月订单ID',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先名',
  `year` int NOT NULL COMMENT '年',
  `month` int NOT NULL COMMENT '月',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '製品別名',
  `product_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '量産品' COMMENT '製品種別（量産品/試作品/補給品/その他）',
  `forecast_units` int DEFAULT '0' COMMENT '内示本数',
  `forecast_total_units` int DEFAULT '0' COMMENT '日内示合計',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '受注ID',
  `forecast_diff` int DEFAULT '0' COMMENT '内示差異（日内示合計-内示本数 ）',
  PRIMARY KEY (`id`,`order_id`) USING BTREE,
  UNIQUE KEY `uq_order_monthly_order_id` (`order_id`) USING BTREE,
  KEY `idx_order_monthly_destination` (`destination_cd`,`year`,`month`) USING BTREE,
  KEY `idx_order_monthly_product` (`product_cd`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC COMMENT='月別受注テーブル';

SET FOREIGN_KEY_CHECKS = 1;
