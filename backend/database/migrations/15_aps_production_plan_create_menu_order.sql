-- APS「生産計画作成」配下メニューの表示順を工程順に揃える
-- 切断 → 成型 → 溶接 → メッキ（menuConfig / SidebarMenu と整合）

UPDATE menus SET sort_order = 1 WHERE code = 'APS_CUTTING_PLANNING';
UPDATE menus SET sort_order = 2 WHERE code = 'APS_PLANNING';
UPDATE menus SET sort_order = 3 WHERE code = 'APS_WELDING_PLANNING';
UPDATE menus SET sort_order = 4 WHERE code = 'APS_PLATING_PLANNING';
