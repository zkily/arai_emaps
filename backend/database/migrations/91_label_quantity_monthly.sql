-- ラベル枚数管理（月度：月初在庫・发行予定）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `label_quantity_monthly` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `year_month` CHAR(7) NOT NULL COMMENT '対象月 YYYY-MM',
  `label_type` VARCHAR(20) NOT NULL COMMENT 'molding / product_use',
  `product_cd` VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `opening_stock` INT NOT NULL DEFAULT 0 COMMENT '月初在庫枚数',
  `opening_locked` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '月初在庫手動ロック（1=再計算で上書きしない）',
  `issue_qty` INT NOT NULL DEFAULT 0 COMMENT '発行予定(紙枚数)（CEIL(max(0,必要−発行済)/6)、1紙=6枚）',
  `issued_qty` INT NOT NULL DEFAULT 0 COMMENT '発行済枚数（印刷実績の累計）',
  `last_issue_history` VARCHAR(255) NULL COMMENT '最終発行・印刷履歴',
  `updated_by` VARCHAR(50) NULL COMMENT '更新者',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_label_qty_month_type_cd` (`year_month`, `label_type`, `product_cd`),
  KEY `idx_label_qty_year_month` (`year_month`),
  KEY `idx_label_qty_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ラベル枚数管理（月度）';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'MASTER_LABEL_QTY_MGMT', 'ラベル枚数管理', p.id, '/master/label-quantity', 'DataAnalysis', 3, 1
FROM menus p
WHERE p.code = 'MASTER_LABEL'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus label_parent ON label_parent.code = 'MASTER_LABEL'
SET cfg.name = 'ラベル枚数管理',
    cfg.parent_id = label_parent.id,
    cfg.path = '/master/label-quantity',
    cfg.icon = 'DataAnalysis',
    cfg.sort_order = 3,
    cfg.is_active = 1
WHERE cfg.code = 'MASTER_LABEL_QTY_MGMT';

-- 親メニュー権限を持つロールに付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, qty.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'MASTER_LABEL'
INNER JOIN menus qty ON qty.code = 'MASTER_LABEL_QTY_MGMT';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, qty.id
FROM role_menu_permissions rmp
INNER JOIN menus cfg ON cfg.id = rmp.menu_id
  AND cfg.code IN ('MASTER_PRODUCT_LABEL_CONFIG', 'MASTER_PRODUCT_USE_LABEL_CONFIG')
INNER JOIN menus qty ON qty.code = 'MASTER_LABEL_QTY_MGMT';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), m.id
FROM menus m
WHERE m.code = 'MASTER_LABEL_QTY_MGMT';
