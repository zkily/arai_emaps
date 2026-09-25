-- 品質管理 > 製品関連：生産注意事項（工程別）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `quality_product_process_cautions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_code` VARCHAR(20) NOT NULL COMMENT '工程 cutting/chamfering/forming/welding/plating/inspection',
  `product_cd` VARCHAR(50) NULL COMMENT '製品CD（NULL=工程共通）',
  `product_name` VARCHAR(200) NULL COMMENT '製品名',
  `caution_text` VARCHAR(500) NOT NULL COMMENT '注意事項テキスト',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=有効',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '並び',
  `created_by` VARCHAR(64) NULL COMMENT '登録者',
  `updated_by` VARCHAR(64) NULL COMMENT '更新者',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_qppc_process` (`process_code`, `is_active`, `sort_order`),
  KEY `idx_qppc_product` (`product_cd`, `process_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='製品生産注意事項（工程別）';

-- 製品関連を親メニュー化（パスなし）
UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_QUALITY'
SET cfg.name = '製品関連',
    cfg.parent_id = parent.id,
    cfg.path = NULL,
    cfg.icon = 'Goods',
    cfg.sort_order = 2
WHERE cfg.code = 'ERP_QUALITY_PRODUCT';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_QUALITY_PRODUCT_PROCESS_CAUTION', '生産注意事項', m.id,
       '/erp/quality/product-association/process-cautions', 'Warning', 1
FROM menus m
WHERE m.code = 'ERP_QUALITY_PRODUCT'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_QUALITY_PRODUCT'
SET cfg.name = '生産注意事項',
    cfg.parent_id = parent.id,
    cfg.path = '/erp/quality/product-association/process-cautions',
    cfg.icon = 'Warning',
    cfg.sort_order = 1
WHERE cfg.code = 'ERP_QUALITY_PRODUCT_PROCESS_CAUTION';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'ERP_QUALITY_PRODUCT'
INNER JOIN menus child ON child.code = 'ERP_QUALITY_PRODUCT_PROCESS_CAUTION';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_QUALITY_PRODUCT_PROCESS_CAUTION';
