-- APS: 生産計画作成 配下に「メッキ計画作成」を追加

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_PLATING_PLANNING', 'メッキ計画作成', m.id, '/aps/plating-planning', 'Operation', 4
FROM menus m
WHERE m.code = 'APS_PRODUCTION_PLAN_CREATE'
LIMIT 1;

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'APS_PRODUCTION_PLAN_CREATE'
INNER JOIN menus child ON child.code = 'APS_PLATING_PLANNING';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_PLATING_PLANNING';
