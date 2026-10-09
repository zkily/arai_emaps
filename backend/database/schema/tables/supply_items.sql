-- TABLE: supply_items
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `supply_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '備品CD',
  `item_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '備品名',
  `specification` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '規格',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '個' COMMENT '単位',
  `pack_qty` int NOT NULL DEFAULT '1' COMMENT '個数（入り数）',
  `order_lot` int NOT NULL DEFAULT '1' COMMENT '注文ロット',
  `unit_price` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '単価',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '仕入先CD',
  `is_discontinued` tinyint(1) NOT NULL DEFAULT '0' COMMENT '終息',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supply_item_supplier` (`supplier_cd`,`item_cd`),
  KEY `idx_supply_items_supplier` (`supplier_cd`),
  KEY `idx_supply_items_item_cd` (`item_cd`),
  KEY `idx_supply_items_discontinued` (`is_discontinued`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='備品マスタ（仕入先別カタログ）';

SET FOREIGN_KEY_CHECKS = 1;
