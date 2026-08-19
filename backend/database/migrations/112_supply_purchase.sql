-- 備品購入：仕入先別カタログ + 発注ヘッダ/明細（購買情報レコード型）
-- 購買・外注管理 > 備品購入（menuConfig と整合）

CREATE TABLE IF NOT EXISTS `supply_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '備品CD',
  `item_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '備品名',
  `specification` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '個' COMMENT '単位',
  `pack_qty` int NOT NULL DEFAULT 1 COMMENT '個数（入り数）',
  `order_lot` int NOT NULL DEFAULT 1 COMMENT '注文ロット',
  `unit_price` decimal(12, 2) NOT NULL DEFAULT 0.00 COMMENT '単価',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '仕入先CD',
  `is_discontinued` tinyint(1) NOT NULL DEFAULT 0 COMMENT '終息',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supply_item_supplier` (`supplier_cd`, `item_cd`),
  KEY `idx_supply_items_supplier` (`supplier_cd`),
  KEY `idx_supply_items_item_cd` (`item_cd`),
  KEY `idx_supply_items_discontinued` (`is_discontinued`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='備品マスタ（仕入先別カタログ）';

CREATE TABLE IF NOT EXISTS `supply_purchase_orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '発注番号',
  `order_date` date NOT NULL COMMENT '発注日',
  `delivery_date` date NULL DEFAULT NULL COMMENT '納入日',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '仕入先CD',
  `supplier_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '仕入先名',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ordered' COMMENT 'ordered/cancelled',
  `total_amount` decimal(14, 2) NOT NULL DEFAULT 0.00 COMMENT '合計金額',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supply_po_no` (`order_no`),
  KEY `idx_supply_po_supplier` (`supplier_cd`),
  KEY `idx_supply_po_date` (`order_date`),
  KEY `idx_supply_po_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='備品発注ヘッダ';

CREATE TABLE IF NOT EXISTS `supply_purchase_order_lines` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL COMMENT '発注ヘッダID',
  `line_no` int NOT NULL DEFAULT 1 COMMENT '行番号',
  `item_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '備品CD',
  `item_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '備品名',
  `specification` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '個' COMMENT '単位',
  `pack_qty` int NOT NULL DEFAULT 1 COMMENT '個数（入り数）',
  `order_lot` int NOT NULL DEFAULT 1 COMMENT '注文ロット',
  `order_qty` int NOT NULL COMMENT '発注数量',
  `unit_price` decimal(12, 2) NOT NULL DEFAULT 0.00 COMMENT '単価（発注時点）',
  `amount` decimal(14, 2) NOT NULL DEFAULT 0.00 COMMENT '金額',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_supply_po_line_order` (`order_id`),
  CONSTRAINT `fk_supply_po_line_order`
    FOREIGN KEY (`order_id`) REFERENCES `supply_purchase_orders` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='備品発注明細';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_PURCHASE_SUPPLIES', '備品購入', m.id, '/erp/purchase/supplies', 'Box', 4
FROM menus m
WHERE m.code = 'ERP_PURCHASE'
LIMIT 1;

UPDATE menus child
INNER JOIN menus parent ON parent.code = 'ERP_PURCHASE'
SET child.name = '備品購入',
    child.path = '/erp/purchase/supplies',
    child.icon = 'Box',
    child.sort_order = 4,
    child.parent_id = parent.id,
    child.is_active = 1
WHERE child.code = 'ERP_PURCHASE_SUPPLIES';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT rmp.role_id, new_menu.id
FROM role_menu_permissions rmp
INNER JOIN menus sibling ON sibling.id = rmp.menu_id AND sibling.code = 'ERP_PURCHASE_PART_ORDER'
INNER JOIN menus new_menu ON new_menu.code = 'ERP_PURCHASE_SUPPLIES';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT rmp.role_id, new_menu.id
FROM role_menu_permissions rmp
INNER JOIN menus sibling ON sibling.id = rmp.menu_id AND sibling.code = 'ERP_PURCHASE_MATERIAL_ORDER'
INNER JOIN menus new_menu ON new_menu.code = 'ERP_PURCHASE_SUPPLIES'
WHERE NOT EXISTS (
  SELECT 1
  FROM role_menu_permissions x
  INNER JOIN menus m ON m.id = x.menu_id
  WHERE m.code = 'ERP_PURCHASE_SUPPLIES'
);

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_PURCHASE_SUPPLIES';
