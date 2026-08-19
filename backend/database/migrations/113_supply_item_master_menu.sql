-- マスタ > 備品マスタ（supply_items 管理画面）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MASTER_SUPPLY_ITEM', '備品マスタ', m.id, '/master/supply-item', 'Box', 4
FROM menus m
WHERE m.code = 'MASTER_LIST'
LIMIT 1;

UPDATE menus child
INNER JOIN menus parent ON parent.code = 'MASTER_LIST'
SET child.name = '備品マスタ',
    child.path = '/master/supply-item',
    child.icon = 'Box',
    child.sort_order = 4,
    child.parent_id = parent.id,
    child.is_active = 1
WHERE child.code = 'MASTER_SUPPLY_ITEM';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT rmp.role_id, new_menu.id
FROM role_menu_permissions rmp
INNER JOIN menus sibling ON sibling.id = rmp.menu_id AND sibling.code = 'MASTER_SUPPLIER'
INNER JOIN menus new_menu ON new_menu.code = 'MASTER_SUPPLY_ITEM';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'MASTER_SUPPLY_ITEM';
