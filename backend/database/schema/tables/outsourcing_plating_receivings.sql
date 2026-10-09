-- TABLE: outsourcing_plating_receivings
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `outsourcing_plating_receivings` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '受入ID',
  `receiving_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '受入番号',
  `receiving_date` date NOT NULL COMMENT '受入日',
  `order_id` int NOT NULL COMMENT '注文ID',
  `order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '注文番号',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品名',
  `plating_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'メッキ種類',
  `order_qty` int NOT NULL COMMENT '注文数量',
  `receiving_qty` int NOT NULL COMMENT '受入数量',
  `good_qty` int DEFAULT '0' COMMENT '良品数量',
  `defect_qty` int DEFAULT '0' COMMENT '不良数量',
  `defect_reason` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '不良理由',
  `status` enum('pending','inspected','defect') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'pending' COMMENT '検収状態',
  `inspector` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '検収者',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `delivery_location` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '納入場所',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '区分',
  `content` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '内容',
  `specification` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '規格',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `receiving_no` (`receiving_no`) USING BTREE,
  KEY `idx_receiving_no` (`receiving_no`) USING BTREE,
  KEY `idx_receiving_date` (`receiving_date`) USING BTREE,
  KEY `idx_order_id` (`order_id`) USING BTREE,
  KEY `idx_supplier_cd` (`supplier_cd`) USING BTREE,
  KEY `idx_status` (`status`) USING BTREE,
  CONSTRAINT `outsourcing_plating_receivings_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `outsourcing_plating_orders` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='外注メッキ受入';

SET FOREIGN_KEY_CHECKS = 1;
