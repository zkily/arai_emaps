SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for suppliers (マスタ用)
-- ----------------------------
DROP TABLE IF EXISTS `suppliers`;
CREATE TABLE `suppliers` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `supplier_cd` varchar(50) NOT NULL COMMENT '仕入先CD',
  `supplier_name` varchar(100) NOT NULL COMMENT '仕入先名',
  `supplier_kana` varchar(100) DEFAULT NULL COMMENT '仕入先カナ',
  `contact_person` varchar(100) DEFAULT NULL COMMENT '担当者',
  `phone` varchar(20) DEFAULT NULL COMMENT '電話番号',
  `fax` varchar(20) DEFAULT NULL COMMENT 'FAX番号',
  `email` varchar(100) DEFAULT NULL COMMENT 'メールアドレス',
  `postal_code` varchar(10) DEFAULT NULL COMMENT '郵便番号',
  `address1` varchar(200) DEFAULT NULL COMMENT '住所1',
  `address2` varchar(200) DEFAULT NULL COMMENT '住所2',
  `payment_terms` varchar(50) DEFAULT NULL COMMENT '支払条件',
  `currency` varchar(10) DEFAULT 'JPY' COMMENT '通貨',
  `remarks` text COMMENT '備考',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supplier_cd` (`supplier_cd`),
  KEY `idx_supplier_name` (`supplier_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='仕入先マスタ';

SET FOREIGN_KEY_CHECKS = 1;
