-- TABLE: supply_purchase_orders
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `supply_purchase_orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '発注番号',
  `order_date` date NOT NULL COMMENT '発注日',
  `delivery_date` date DEFAULT NULL COMMENT '納入日',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '仕入先CD',
  `supplier_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '仕入先名',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ordered' COMMENT 'ordered/cancelled',
  `total_amount` decimal(14,2) NOT NULL DEFAULT '0.00' COMMENT '合計金額',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supply_po_no` (`order_no`),
  KEY `idx_supply_po_supplier` (`supplier_cd`),
  KEY `idx_supply_po_date` (`order_date`),
  KEY `idx_supply_po_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='備品発注ヘッダ';

SET FOREIGN_KEY_CHECKS = 1;
