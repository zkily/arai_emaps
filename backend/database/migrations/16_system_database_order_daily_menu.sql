-- システム管理 > データベース > order_daily（menuConfig / SidebarMenu と整合）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'SYSTEM_DATABASE', 'データベース', m.id, NULL, 'Coin', 3
FROM menus m
WHERE m.code = 'SYSTEM'
LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'SYSTEM_DB_ORDER_DAILY', 'order_daily', m.id, '/system/database/order/daily', 'List', 1
FROM menus m
WHERE m.code = 'SYSTEM_DATABASE'
LIMIT 1;
