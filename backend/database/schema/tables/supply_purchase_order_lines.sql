-- TABLE: supply_purchase_order_lines
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `supply_purchase_order_lines` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL COMMENT '発注ヘッダID',
  `line_no` int NOT NULL DEFAULT '1' COMMENT '行番号',
  `item_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '備品CD',
  `item_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備品名',
  `specification` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '規格',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '個' COMMENT '単位',
  `pack_qty` int NOT NULL DEFAULT '1' COMMENT '個数（入り数）',
  `order_lot` int NOT NULL DEFAULT '1' COMMENT '注文ロット',
  `order_qty` int NOT NULL COMMENT '発注数量',
  `unit_price` decimal(12,2) NOT NULL DEFAULT '0.00' COMMENT '単価（発注時点）',
  `amount` decimal(14,2) NOT NULL DEFAULT '0.00' COMMENT '金額',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_supply_po_line_order` (`order_id`),
  CONSTRAINT `fk_supply_po_line_order` FOREIGN KEY (`order_id`) REFERENCES `supply_purchase_orders` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='備品発注明細';

SET FOREIGN_KEY_CHECKS = 1;
