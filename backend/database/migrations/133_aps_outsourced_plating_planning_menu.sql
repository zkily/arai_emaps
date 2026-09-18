-- APS「生産計画作成」配下に外注メッキ計画作成を追加

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_OUTSOURCED_PLATING_PLANNING', '外注メッキ計画作成', m.id, '/aps/outsourced-plating-planning', 'Brush', 5
FROM menus m
WHERE m.code = 'APS_PRODUCTION_PLAN_CREATE'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'APS_PRODUCTION_PLAN_CREATE'
SET cfg.name = '外注メッキ計画作成',
    cfg.parent_id = parent.id,
    cfg.path = '/aps/outsourced-plating-planning',
    cfg.icon = 'Brush',
    cfg.sort_order = 5
WHERE cfg.code = 'APS_OUTSOURCED_PLATING_PLANNING';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'APS_PRODUCTION_PLAN_CREATE'
INNER JOIN menus child ON child.code = 'APS_OUTSOURCED_PLATING_PLANNING';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_OUTSOURCED_PLATING_PLANNING';
