-- TABLE: sales_contract_pricing
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `sales_contract_pricing` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `customer_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '顧客名',
  `product_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品名',
  `contract_price` decimal(12,2) NOT NULL COMMENT '契約単価',
  `standard_price` decimal(12,2) DEFAULT NULL COMMENT '標準単価',
  `discount_rate` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT '割引率',
  `valid_from` date NOT NULL COMMENT '適用開始日',
  `valid_until` date DEFAULT NULL COMMENT '適用終了日',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT 'active/expired/cancelled',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_scp_cust_prod_from` (`customer_code`,`product_code`,`valid_from`),
  KEY `idx_scp_customer` (`customer_code`),
  KEY `idx_scp_product` (`product_code`),
  KEY `idx_scp_status` (`status`),
  KEY `idx_scp_valid` (`valid_from`,`valid_until`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='契約単価';

SET FOREIGN_KEY_CHECKS = 1;
