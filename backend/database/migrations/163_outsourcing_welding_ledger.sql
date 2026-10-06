-- 外注溶接日別台帳（外注メッキ台帳と同じ構成。在庫取引は KT08 / KT16、単位は本）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `outsourcing_welding_ledger` (
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
  `order_sheet_issued_at` datetime NULL COMMENT '注文書発行日時',
  `order_sheet_issued_by` varchar(100) NULL COMMENT '注文書発行者',
  `receiving_qty` int NULL DEFAULT 0 COMMENT '受入数',
  `receiving_no` varchar(30) NULL COMMENT '受入管理番号',
  `defect_qty` int NULL DEFAULT 0 COMMENT '不良数',
  `disposal_no` varchar(30) NULL COMMENT '不良管理番号',
  `initial_stock` int NULL DEFAULT 0 COMMENT '初期在庫',
  `current_stock` int NULL DEFAULT 0 COMMENT '現在庫（外注先手元）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_welding_ledger_day` (`order_date`, `supplier_cd`, `product_cd`),
  UNIQUE KEY `uk_welding_ledger_order_no` (`order_no`),
  UNIQUE KEY `uk_welding_ledger_receiving_no` (`receiving_no`),
  UNIQUE KEY `uk_welding_ledger_disposal_no` (`disposal_no`),
  KEY `idx_welding_ledger_supplier` (`supplier_cd`),
  KEY `idx_welding_ledger_product` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外注溶接日別台帳';
