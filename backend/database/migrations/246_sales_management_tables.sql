-- 販売管理追加テーブル（見積・請求書・与信・契約単価・内示）
-- 例: mysql -u USER -p eams_db < backend/database/migrations/246_sales_management_tables.sql
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 見積テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_quotation` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `quotation_no` varchar(50) NOT NULL COMMENT '見積番号',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `quotation_date` date NOT NULL COMMENT '見積日',
  `valid_until` date DEFAULT NULL COMMENT '有効期限',
  `status` varchar(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/sent/accepted/rejected/expired',
  `subtotal` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '小計',
  `tax_rate` decimal(5,2) NOT NULL DEFAULT 10 COMMENT '税率',
  `tax_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '税額',
  `total_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '合計金額',
  `sales_person` varchar(100) DEFAULT NULL COMMENT '営業担当者',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sq_quotation_no` (`quotation_no`),
  KEY `idx_sq_customer` (`customer_code`),
  KEY `idx_sq_date` (`quotation_date`),
  KEY `idx_sq_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='見積';

-- ---------------------------------------------------------------------------
-- 見積明細テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_quotation_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `quotation_id` int NOT NULL COMMENT 'sales_quotation.id',
  `line_no` int NOT NULL COMMENT '行番号',
  `product_code` varchar(100) NOT NULL COMMENT '品番',
  `product_name` varchar(300) DEFAULT NULL COMMENT '品名',
  `specification` varchar(500) DEFAULT NULL COMMENT '仕様',
  `unit` varchar(20) NOT NULL DEFAULT '個' COMMENT '単位',
  `quantity` int NOT NULL COMMENT '数量',
  `unit_price` decimal(12,2) NOT NULL COMMENT '単価',
  `tax_rate` decimal(5,2) NOT NULL DEFAULT 10 COMMENT '税率',
  `amount` decimal(15,2) NOT NULL COMMENT '金額',
  `remarks` text COMMENT '備考',
  PRIMARY KEY (`id`),
  KEY `idx_sqi_quotation` (`quotation_id`),
  KEY `idx_sqi_product` (`product_code`),
  CONSTRAINT `fk_sqi_quotation` FOREIGN KEY (`quotation_id`) REFERENCES `sales_quotation` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='見積明細';

-- ---------------------------------------------------------------------------
-- 請求書テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_invoice` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `invoice_no` varchar(50) NOT NULL COMMENT '請求書番号',
  `order_id` int DEFAULT NULL COMMENT '受注ID',
  `order_no` varchar(50) DEFAULT NULL COMMENT '受注番号',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `invoice_date` date NOT NULL COMMENT '請求日',
  `due_date` date DEFAULT NULL COMMENT '支払期限',
  `status` varchar(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/issued/paid/overdue/cancelled',
  `subtotal` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '小計',
  `tax_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '税額',
  `total_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '合計金額',
  `paid_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '入金済金額',
  `payment_method` varchar(50) DEFAULT NULL COMMENT '支払方法',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `issued_at` datetime DEFAULT NULL COMMENT '発行日時',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_si_invoice_no` (`invoice_no`),
  KEY `idx_si_order` (`order_id`),
  KEY `idx_si_customer` (`customer_code`),
  KEY `idx_si_date` (`invoice_date`),
  KEY `idx_si_due_date` (`due_date`),
  KEY `idx_si_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='請求書';

-- ---------------------------------------------------------------------------
-- 請求書明細テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_invoice_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `invoice_id` int NOT NULL COMMENT 'sales_invoice.id',
  `line_no` int NOT NULL COMMENT '行番号',
  `product_code` varchar(100) NOT NULL COMMENT '品番',
  `product_name` varchar(300) DEFAULT NULL COMMENT '品名',
  `unit` varchar(20) NOT NULL DEFAULT '個' COMMENT '単位',
  `quantity` int NOT NULL COMMENT '数量',
  `unit_price` decimal(12,2) NOT NULL COMMENT '単価',
  `tax_rate` decimal(5,2) NOT NULL DEFAULT 10 COMMENT '税率',
  `amount` decimal(15,2) NOT NULL COMMENT '金額',
  `remarks` text COMMENT '備考',
  PRIMARY KEY (`id`),
  KEY `idx_sii_invoice` (`invoice_id`),
  KEY `idx_sii_product` (`product_code`),
  CONSTRAINT `fk_sii_invoice` FOREIGN KEY (`invoice_id`) REFERENCES `sales_invoice` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='請求書明細';

-- ---------------------------------------------------------------------------
-- 与信管理テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_credit` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `credit_limit` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '与信限度額',
  `current_balance` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '現在残高',
  `available_credit` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '利用可能額',
  `risk_level` varchar(20) NOT NULL DEFAULT 'low' COMMENT 'low/medium/high/blocked',
  `last_review_date` date DEFAULT NULL COMMENT '前回審査日',
  `next_review_date` date DEFAULT NULL COMMENT '次回審査日',
  `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT 'active/suspended/blocked',
  `remarks` text COMMENT '備考',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sc_customer` (`customer_code`),
  KEY `idx_sc_risk_level` (`risk_level`),
  KEY `idx_sc_status` (`status`),
  KEY `idx_sc_next_review` (`next_review_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='与信管理';

-- ---------------------------------------------------------------------------
-- 契約単価テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_contract_pricing` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `product_code` varchar(100) NOT NULL COMMENT '品番',
  `product_name` varchar(300) DEFAULT NULL COMMENT '品名',
  `contract_price` decimal(12,2) NOT NULL COMMENT '契約単価',
  `standard_price` decimal(12,2) DEFAULT NULL COMMENT '標準単価',
  `discount_rate` decimal(5,2) NOT NULL DEFAULT 0 COMMENT '割引率',
  `valid_from` date NOT NULL COMMENT '適用開始日',
  `valid_until` date DEFAULT NULL COMMENT '適用終了日',
  `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT 'active/expired/cancelled',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_scp_cust_prod_from` (`customer_code`, `product_code`, `valid_from`),
  KEY `idx_scp_customer` (`customer_code`),
  KEY `idx_scp_product` (`product_code`),
  KEY `idx_scp_status` (`status`),
  KEY `idx_scp_valid` (`valid_from`, `valid_until`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='契約単価';

-- ---------------------------------------------------------------------------
-- 内示テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_forecast` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `product_code` varchar(100) NOT NULL COMMENT '品番',
  `product_name` varchar(300) DEFAULT NULL COMMENT '品名',
  `forecast_month` char(7) NOT NULL COMMENT '内示月 (YYYY-MM)',
  `forecast_quantity` int NOT NULL DEFAULT 0 COMMENT '内示数量',
  `confirmed_quantity` int NOT NULL DEFAULT 0 COMMENT '確定数量',
  `status` varchar(20) NOT NULL DEFAULT 'forecast' COMMENT 'forecast/confirmed/revised',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sf_cust_prod_month` (`customer_code`, `product_code`, `forecast_month`),
  KEY `idx_sf_customer` (`customer_code`),
  KEY `idx_sf_product` (`product_code`),
  KEY `idx_sf_month` (`forecast_month`),
  KEY `idx_sf_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内示';
