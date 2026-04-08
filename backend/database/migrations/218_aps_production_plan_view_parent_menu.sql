-- APS：親メニュー「生産計画一覧」を APS 直下に追加し、「成型計画一覧」をその配下へ移す（menuConfig / Sidebar 整合）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_PRODUCTION_PLAN_VIEW', '生産計画一覧', m.id, NULL, 'List', 1.5
FROM menus m
WHERE m.code = 'APS'
LIMIT 1;

UPDATE menus child
INNER JOIN menus new_parent ON new_parent.code = 'APS_PRODUCTION_PLAN_VIEW'
SET child.parent_id = new_parent.id, child.sort_order = 1
WHERE child.code = 'APS_FORMING_PLAN_LIST';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id AND c.code = 'APS_FORMING_PLAN_LIST'
INNER JOIN menus p ON p.code = 'APS_PRODUCTION_PLAN_VIEW';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_PRODUCTION_PLAN_VIEW';
