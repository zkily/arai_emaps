-- 出荷管理 > 出荷パレット数管理（menuConfig / SidebarMenu と整合）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_SHIPPING_PALLET_COUNT', '出荷パレット数管理', m.id, '/erp/shipping/pallet-count', 'Grid', 2
FROM menus m
WHERE m.code = 'ERP_SHIPPING'
LIMIT 1;

UPDATE menus child
INNER JOIN menus parent ON parent.code = 'ERP_SHIPPING'
SET child.name = '出荷パレット数管理',
    child.path = '/erp/shipping/pallet-count',
    child.icon = 'Grid',
    child.sort_order = 2,
    child.parent_id = parent.id,
    child.is_active = 1
WHERE child.code = 'ERP_SHIPPING_PALLET_COUNT';

-- 出荷構成表管理と同じロールにメニュー権限を付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT rmp.role_id, new_menu.id
FROM role_menu_permissions rmp
INNER JOIN menus sibling ON sibling.id = rmp.menu_id AND sibling.code = 'ERP_SHIPPING_LIST'
INNER JOIN menus new_menu ON new_menu.code = 'ERP_SHIPPING_PALLET_COUNT';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_SHIPPING_PALLET_COUNT';
