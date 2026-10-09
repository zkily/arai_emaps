-- TABLE: sales_quotation
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `sales_quotation` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `quotation_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '見積番号',
  `customer_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '顧客名',
  `quotation_date` date NOT NULL COMMENT '見積日',
  `valid_until` date DEFAULT NULL COMMENT '有効期限',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft' COMMENT 'draft/sent/accepted/rejected/expired',
  `subtotal` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '小計',
  `tax_rate` decimal(5,2) NOT NULL DEFAULT '10.00' COMMENT '税率',
  `tax_amount` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '税額',
  `total_amount` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT '合計金額',
  `sales_person` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '営業担当者',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sq_quotation_no` (`quotation_no`),
  KEY `idx_sq_customer` (`customer_code`),
  KEY `idx_sq_date` (`quotation_date`),
  KEY `idx_sq_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='見積';

SET FOREIGN_KEY_CHECKS = 1;
