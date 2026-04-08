-- APS：生産計画作成配下に「成型計画一覧」を追加（/aps/planning-list）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_FORMING_PLAN_LIST', '成型計画一覧', m.id, '/aps/planning-list', 'List', 3
FROM menus m
WHERE m.code = 'APS_PRODUCTION_PLAN_CREATE'
LIMIT 1;

-- 成型計画作成と同じロールに一覧メニューを付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'APS_PLANNING'
INNER JOIN menus child ON child.code = 'APS_FORMING_PLAN_LIST';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_FORMING_PLAN_LIST';
