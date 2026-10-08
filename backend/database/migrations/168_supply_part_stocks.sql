-- 補給品在庫台帳（在庫カード + 入出庫明細）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `supply_part_stocks` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品別名',
  `part_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品番（かんばん）',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '納入先名',
  `storage_location` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '保管場所',
  `shelf_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '棚番',
  `keeper` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '担当',
  `safety_stock` int NOT NULL DEFAULT 0 COMMENT '安全在庫',
  `on_hand_qty` int NOT NULL DEFAULT 0 COMMENT '現在庫（明細合計）',
  `next_production_date` date NULL DEFAULT NULL COMMENT '次回生産予定日',
  `next_production_qty` int NOT NULL DEFAULT 0 COMMENT '生産予定数量',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `source` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '登録元（transfer/manual）',
  `created_by_user_id` int NULL DEFAULT NULL COMMENT '登録者ID',
  `updated_by_user_id` int NULL DEFAULT NULL COMMENT '更新者ID',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supply_part_product_cd` (`product_cd`),
  INDEX `idx_supply_part_location` (`storage_location`),
  INDEX `idx_supply_part_name` (`product_name`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '補給品在庫カード' ROW_FORMAT = Dynamic;

CREATE TABLE IF NOT EXISTS `supply_part_transactions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `stock_id` bigint NOT NULL COMMENT '在庫カードID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `txn_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'transfer_in/manual_in/production_in/shipment_out/adjust',
  `quantity` int NOT NULL DEFAULT 0 COMMENT '数量（入庫プラス、出庫マイナス）',
  `balance_after` int NOT NULL DEFAULT 0 COMMENT '発生後残高',
  `occurred_date` date NOT NULL COMMENT '発生日',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_by_user_id` int NULL DEFAULT NULL COMMENT '登録者ID',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  INDEX `idx_supply_txn_stock` (`stock_id`),
  INDEX `idx_supply_txn_product` (`product_cd`),
  INDEX `idx_supply_txn_date` (`occurred_date`),
  CONSTRAINT `fk_supply_txn_stock` FOREIGN KEY (`stock_id`) REFERENCES `supply_part_stocks` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '補給品入出庫明細' ROW_FORMAT = Dynamic;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'ERP_INVENTORY_SUPPLY_PARTS', '補給品管理', m.id, '/erp/inventory/supply-parts', 'Box', 4, 1
FROM menus m
WHERE m.code = 'ERP_INVENTORY'
LIMIT 1;

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, newm.id
FROM role_menu_permissions rmp
INNER JOIN menus existing ON existing.id = rmp.menu_id
  AND (existing.code = 'ERP_INVENTORY' OR existing.code LIKE 'ERP_INVENTORY\_%' ESCAPE '\\')
INNER JOIN menus newm ON newm.code = 'ERP_INVENTORY_SUPPLY_PARTS';

SET FOREIGN_KEY_CHECKS = 1;
