-- APS：生産計画一覧配下に「溶接計画一覧」を追加（/aps/welding-planning-list）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_WELDING_PLAN_LIST', '溶接計画一覧', m.id, '/aps/welding-planning-list', 'List', 2
FROM menus m
WHERE m.code = 'APS_PRODUCTION_PLAN_VIEW'
LIMIT 1;

-- 成型計画一覧と同じロールに付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus sibling ON sibling.id = rmp.menu_id AND sibling.code = 'APS_FORMING_PLAN_LIST'
INNER JOIN menus child ON child.code = 'APS_WELDING_PLAN_LIST';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_WELDING_PLAN_LIST';
