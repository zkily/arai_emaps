-- APS メニュー表示順：設備稼働管理 → スケジューリング → APSロット計画（menuConfig / SidebarMenu と整合）

UPDATE menus SET sort_order = 4 WHERE code = 'APS_SCHEDULING';
UPDATE menus SET sort_order = 5 WHERE code = 'APS_BATCH_PLANS';
