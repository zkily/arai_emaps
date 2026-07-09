-- 成型用ラベル設定を マスタ管理 > ラベル発行 配下へ配置（menuConfig と整合）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'MASTER_LABEL', 'ラベル発行', m.id, NULL, 'Printer', 3, 1
FROM menus m
WHERE m.code = 'MASTER'
LIMIT 1;

UPDATE menus child
INNER JOIN menus parent ON parent.code = 'MASTER'
SET child.name = 'ラベル発行',
    child.parent_id = parent.id,
    child.path = NULL,
    child.icon = 'Printer',
    child.sort_order = 3,
    child.is_active = 1
WHERE child.code = 'MASTER_LABEL';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'MASTER_PRODUCT_LABEL_CONFIG', '成型用ラベル設定', p.id, '/master/product-label-config', 'PriceTag', 1, 1
FROM menus p
WHERE p.code = 'MASTER_LABEL'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus label_parent ON label_parent.code = 'MASTER_LABEL'
SET cfg.name = '成型用ラベル設定',
    cfg.parent_id = label_parent.id,
    cfg.path = '/master/product-label-config',
    cfg.icon = 'PriceTag',
    cfg.sort_order = 1,
    cfg.is_active = 1
WHERE cfg.code = 'MASTER_PRODUCT_LABEL_CONFIG';

-- 親メニュー権限：成型用ラベル設定を持つロールに付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, label_menu.id
FROM role_menu_permissions rmp
INNER JOIN menus cfg ON cfg.id = rmp.menu_id AND cfg.code = 'MASTER_PRODUCT_LABEL_CONFIG'
INNER JOIN menus label_menu ON label_menu.code = 'MASTER_LABEL';

-- BOM 配下から移行したロール向け（設定メニュー未登録時）
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, cfg.id
FROM role_menu_permissions rmp
INNER JOIN menus bom ON bom.id = rmp.menu_id AND bom.code = 'MASTER_BOM'
INNER JOIN menus cfg ON cfg.code = 'MASTER_PRODUCT_LABEL_CONFIG'
WHERE NOT EXISTS (
  SELECT 1
  FROM role_menu_permissions x
  INNER JOIN menus m ON m.id = x.menu_id
  WHERE m.code = 'MASTER_PRODUCT_LABEL_CONFIG' AND x.role_id = rmp.role_id
);

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), m.id
FROM menus m
WHERE m.code IN ('MASTER_LABEL', 'MASTER_PRODUCT_LABEL_CONFIG');
