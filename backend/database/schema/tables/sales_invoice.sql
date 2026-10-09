-- TABLE: sales_invoice
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `sales_invoice` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `invoice_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '請求書番号',
  `order_id` int DEFAULT NULL COMMENT '受注ID',
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '受注番号',
  `customer_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '顧客名',
  `invoice_date` date NOT NULL COMMENT '請求日',
  `due_date` date DEFAULT NULL COMMENT '支払期限',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft' COMMENT 'draft/issued/paid/overdue/cancelled',
  `subtotal` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '小計',
  `tax_amount` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '税額',
  `total_amount` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '合計金額',
  `paid_amount` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '入金済金額',
  `payment_method` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '支払方法',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
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

SET FOREIGN_KEY_CHECKS = 1;
