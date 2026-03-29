-- APS: 親メニュー「生産計画作成」を追加し、成型計画作成（APS_PLANNING）のみをその下に置く。
-- スケジューリング等は APS 直下（menuConfig と整合）。

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_PRODUCTION_PLAN_CREATE', '生産計画作成', m.id, NULL, 'Calendar', 1
FROM menus m WHERE m.code = 'APS' LIMIT 1;

UPDATE menus c
INNER JOIN menus p ON p.code = 'APS_PRODUCTION_PLAN_CREATE'
SET c.parent_id = p.id
WHERE c.code = 'APS_PLANNING';

UPDATE menus SET name = '成型計画作成' WHERE code = 'APS_PLANNING';

-- 成型計画メニュー権限を持つロールに親メニュー権限を付与（権限ツリー表示用）
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id AND c.code = 'APS_PLANNING'
INNER JOIN menus p ON p.code = 'APS_PRODUCTION_PLAN_CREATE';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id FROM menus WHERE code = 'APS_PRODUCTION_PLAN_CREATE';
