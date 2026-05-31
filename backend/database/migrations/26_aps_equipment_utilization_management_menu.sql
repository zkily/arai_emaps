-- APS：親メニュー「設備稼働管理」を APS 直下に追加し、設備稼働関連3画面をその配下へ移す（menuConfig / SidebarMenu と整合）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_EQUIPMENT_UTILIZATION_MANAGEMENT', '設備稼働管理', m.id, NULL, 'Setting', 3
FROM menus m
WHERE m.code = 'APS'
LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_CAPACITY_MATRIX', '設備稼働時間表', m.id, '/aps/capacity-matrix', 'Document', 2
FROM menus m
WHERE m.code = 'APS'
LIMIT 1;

UPDATE menus child
INNER JOIN menus new_parent ON new_parent.code = 'APS_EQUIPMENT_UTILIZATION_MANAGEMENT'
SET child.parent_id = new_parent.id,
    child.sort_order = CASE child.code
      WHEN 'APS_CAPACITY' THEN 1
      WHEN 'APS_CAPACITY_MATRIX' THEN 2
      WHEN 'APS_DAILY_REPORT' THEN 3
      ELSE child.sort_order
    END
WHERE child.code IN ('APS_CAPACITY', 'APS_CAPACITY_MATRIX', 'APS_DAILY_REPORT');

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id AND c.code IN ('APS_CAPACITY', 'APS_CAPACITY_MATRIX', 'APS_DAILY_REPORT')
INNER JOIN menus p ON p.code = 'APS_EQUIPMENT_UTILIZATION_MANAGEMENT';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_EQUIPMENT_UTILIZATION_MANAGEMENT';
