-- TABLE: order_daily
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `order_daily` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '日订单ID',
  `monthly_order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '月订单ID（order_monthly的order_id）',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '納入先名',
  `date` date NOT NULL COMMENT '年月日',
  `weekday` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '曜日（日/月/火/水/木/金/土）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `part_number` varchar(50) DEFAULT NULL COMMENT 'EDI かんばん品番（hinban）',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '製品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '製品別名',
  `forecast_units` int DEFAULT '0' COMMENT '内示本数',
  `confirmed_boxes` int DEFAULT '0' COMMENT '確定箱数',
  `confirmed_units` int DEFAULT '0' COMMENT '確定本数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT '未出荷' COMMENT '日別受注ステータス',
  `remarks` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT '' COMMENT '備考',
  `unit_per_box` int DEFAULT '0' COMMENT '1箱あたりの個数',
  `batch_id` int DEFAULT NULL COMMENT '対応する生産バッチID',
  `batch_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT 'バッチ番号（表示用）',
  `supply_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `fulfilled_from_stock` int DEFAULT '0',
  `fulfilled_from_wip` int DEFAULT '0',
  `product_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `confirmed` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否已确认（0:未确认,1:已确认）',
  `confirmed_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '确认人',
  `confirmed_at` datetime DEFAULT NULL COMMENT '确认时间',
  `delivery_date` date DEFAULT NULL COMMENT '納入日（交货日期）',
  `shipping_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  KEY `fk_order_daily_monthly` (`monthly_order_id`) USING BTREE,
  KEY `idx_order_batch_id` (`batch_id`) USING BTREE,
  KEY `idx_order_daily_part_number` (`part_number`),
  CONSTRAINT `order_daily_ibfk_1` FOREIGN KEY (`monthly_order_id`) REFERENCES `order_monthly` (`order_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
