-- 外注メッキ日別台帳：注文日 × 外注先 × 製品 の1行で注文・受入・外注在庫を管理する
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `outsourcing_plating_ledger` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_date` date NOT NULL COMMENT '注文日',
  `supplier_cd` varchar(20) NOT NULL COMMENT '外注先CD',
  `supplier_name` varchar(100) NULL COMMENT '外注先名',
  `product_cd` varchar(50) NOT NULL COMMENT '製品CD',
  `product_name` varchar(200) NULL COMMENT '製品名',
  `unit_price` decimal(12, 2) NULL DEFAULT 0 COMMENT '単価',
  `lead_time_days` int NULL DEFAULT 7 COMMENT '納期計算用リードタイム',
  `delivery_date` date NULL COMMENT '納期',
  `order_qty` int NULL DEFAULT 0 COMMENT '注文数',
  `order_no` varchar(30) NULL COMMENT '注文番号',
  `order_amount` decimal(14, 2) NULL DEFAULT 0 COMMENT '金額',
  `receiving_qty` int NULL DEFAULT 0 COMMENT '受入数',
  `defect_qty` int NULL DEFAULT 0 COMMENT '不良数',
  `initial_stock` int NULL DEFAULT 0 COMMENT '初期在庫',
  `current_stock` int NULL DEFAULT 0 COMMENT '現在庫（外注先手元）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_plating_ledger_day` (`order_date`, `supplier_cd`, `product_cd`),
  UNIQUE KEY `uk_plating_ledger_order_no` (`order_no`),
  KEY `idx_plating_ledger_supplier` (`supplier_cd`),
  KEY `idx_plating_ledger_product` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外注メッキ日別台帳';
