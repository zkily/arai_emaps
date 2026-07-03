-- 生産計画 > 内示帰属管理（menuConfig / SidebarMenu と整合）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_PRODUCTION_LOT_FORECAST_ATTRIBUTION', '内示帰属管理', m.id, '/erp/production/lot-forecast-attribution', 'Calendar', 5
FROM menus m
WHERE m.code = 'ERP_PRODUCTION_PLANNING'
LIMIT 1;

UPDATE menus child
INNER JOIN menus parent ON parent.code = 'ERP_PRODUCTION_PLANNING'
SET child.name = '内示帰属管理',
    child.path = '/erp/production/lot-forecast-attribution',
    child.icon = 'Calendar',
    child.sort_order = 5,
    child.parent_id = parent.id,
    child.is_active = 1
WHERE child.code = 'ERP_PRODUCTION_LOT_FORECAST_ATTRIBUTION';

-- 成型計画試算と同じロールにメニュー権限を付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT rmp.role_id, new_menu.id
FROM role_menu_permissions rmp
INNER JOIN menus sibling ON sibling.id = rmp.menu_id AND sibling.code = 'ERP_PRODUCTION_FORMING_DAILY_PLAN'
INNER JOIN menus new_menu ON new_menu.code = 'ERP_PRODUCTION_LOT_FORECAST_ATTRIBUTION';

-- 成型計画試算が無い環境は生産データ管理の権限をコピー
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT rmp.role_id, new_menu.id
FROM role_menu_permissions rmp
INNER JOIN menus sibling ON sibling.id = rmp.menu_id AND sibling.code = 'ERP_PRODUCTION_DATA'
INNER JOIN menus new_menu ON new_menu.code = 'ERP_PRODUCTION_LOT_FORECAST_ATTRIBUTION'
WHERE NOT EXISTS (
  SELECT 1
  FROM role_menu_permissions x
  INNER JOIN menus m ON m.id = x.menu_id
  WHERE m.code = 'ERP_PRODUCTION_LOT_FORECAST_ATTRIBUTION'
);

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_PRODUCTION_LOT_FORECAST_ATTRIBUTION';
