-- MES「モニタリング」配下に工場レイアウトを追加

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_MONITOR_FACTORY_LAYOUT', '工場レイアウト', m.id, '/mes/monitoring/factory-layout', 'MapLocation', 3
FROM menus m
WHERE m.code = 'MES_MONITORING'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'MES_MONITORING'
SET cfg.name = '工場レイアウト',
    cfg.parent_id = parent.id,
    cfg.path = '/mes/monitoring/factory-layout',
    cfg.icon = 'MapLocation',
    cfg.sort_order = 3
WHERE cfg.code = 'MES_MONITOR_FACTORY_LAYOUT';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'MES_MONITORING'
INNER JOIN menus child ON child.code = 'MES_MONITOR_FACTORY_LAYOUT';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'MES_MONITOR_FACTORY_LAYOUT';
