-- TABLE: outsourcing_plating_ledger
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `outsourcing_plating_ledger` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_date` date NOT NULL COMMENT '注文日',
  `supplier_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先CD',
  `supplier_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '外注先名',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製品名',
  `unit_price` decimal(12,2) DEFAULT '0.00' COMMENT '単価',
  `lead_time_days` int DEFAULT '7' COMMENT '納期計算用リードタイム',
  `delivery_date` date DEFAULT NULL COMMENT '納期',
  `delivery_date_manual` tinyint(1) NOT NULL DEFAULT '0' COMMENT '納期手修正',
  `order_qty` int DEFAULT '0' COMMENT '注文数',
  `order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '注文番号',
  `order_amount` decimal(14,2) DEFAULT '0.00' COMMENT '金額',
  `order_sheet_issued_at` datetime DEFAULT NULL COMMENT '注文書発行日時',
  `order_sheet_issued_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '注文書発行者',
  `receiving_qty` int DEFAULT '0' COMMENT '受入数',
  `receiving_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '受入管理番号',
  `defect_qty` int DEFAULT '0' COMMENT '不良数',
  `disposal_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '不良管理番号',
  `initial_stock` int DEFAULT '0' COMMENT '初期在庫',
  `current_stock` int DEFAULT '0' COMMENT '現在庫（外注先手元）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_plating_ledger_day` (`order_date`,`supplier_cd`,`product_cd`),
  UNIQUE KEY `uk_plating_ledger_order_no` (`order_no`),
  UNIQUE KEY `uk_plating_ledger_receiving_no` (`receiving_no`),
  UNIQUE KEY `uk_plating_ledger_disposal_no` (`disposal_no`),
  KEY `idx_plating_ledger_supplier` (`supplier_cd`),
  KEY `idx_plating_ledger_product` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外注メッキ日別台帳';

SET FOREIGN_KEY_CHECKS = 1;
