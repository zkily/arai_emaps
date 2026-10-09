-- TABLE: sales_quotation_item
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `sales_quotation_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `quotation_id` int NOT NULL COMMENT 'sales_quotation.id',
  `line_no` int NOT NULL COMMENT '行番号',
  `product_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品名',
  `specification` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '仕様',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '個' COMMENT '単位',
  `quantity` int NOT NULL COMMENT '数量',
  `unit_price` decimal(12,2) NOT NULL COMMENT '単価',
  `tax_rate` decimal(5,2) NOT NULL DEFAULT '10.00' COMMENT '税率',
  `amount` decimal(15,2) NOT NULL COMMENT '金額',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  PRIMARY KEY (`id`),
  KEY `idx_sqi_quotation` (`quotation_id`),
  KEY `idx_sqi_product` (`product_code`),
  CONSTRAINT `fk_sqi_quotation` FOREIGN KEY (`quotation_id`) REFERENCES `sales_quotation` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='見積明細';

SET FOREIGN_KEY_CHECKS = 1;
