-- APS 直下に CP-SAT 最適化画面を追加（menuConfig / SidebarMenu と整合）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_CPSAT', 'CP-SAT最適化', m.id, '/aps/cpsat', 'MagicStick', 5
FROM menus m
WHERE m.code = 'APS'
LIMIT 1;

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT rmp.role_id, n.id
FROM role_menu_permissions rmp
INNER JOIN menus o ON o.id = rmp.menu_id AND o.code = 'APS_SCHEDULING'
INNER JOIN menus n ON n.code = 'APS_CPSAT';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_CPSAT';
