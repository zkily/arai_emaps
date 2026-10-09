-- TABLE: sales_order_item
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `sales_order_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '受注明細ID',
  `order_id` int NOT NULL COMMENT '受注ID（sales_order.id）',
  `line_no` int NOT NULL COMMENT '行番号',
  `item_order_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製品別受注番号（親受注番号-品番）',
  `product_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品名',
  `specification` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '仕様',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '個' COMMENT '単位',
  `quantity` int NOT NULL COMMENT '受注数量（本数）',
  `confirmed_boxes` int NOT NULL DEFAULT '0' COMMENT '確定箱数（order_daily.confirmed_boxes）',
  `delivered_quantity` int DEFAULT '0' COMMENT '出荷済数量',
  `unit_price` decimal(12,2) NOT NULL COMMENT '単価',
  `tax_rate` decimal(5,2) DEFAULT '10.00' COMMENT '税率（%）',
  `tax_amount` decimal(12,2) DEFAULT '0.00' COMMENT '税額',
  `amount` decimal(15,2) NOT NULL COMMENT '金額',
  `warehouse_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '倉庫コード',
  `expected_delivery_date` date DEFAULT NULL COMMENT '出荷予定日',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `source_order_daily_id` int DEFAULT NULL COMMENT '同期元日別受注ID（order_daily.id）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_sales_order_item_order_daily` (`source_order_daily_id`),
  KEY `order_id` (`order_id`),
  CONSTRAINT `sales_order_item_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `sales_order` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='受注明細（販売受注の行）';

SET FOREIGN_KEY_CHECKS = 1;
