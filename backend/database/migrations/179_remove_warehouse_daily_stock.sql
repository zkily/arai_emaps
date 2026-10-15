-- 倉庫日次在庫機能削除（画面・メニュー・データテーブル）
SET NAMES utf8mb4;

DELETE rmp
FROM role_menu_permissions rmp
INNER JOIN menus m ON m.id = rmp.menu_id
WHERE m.code = 'ERP_SHIPPING_WAREHOUSE_DAILY';

DELETE FROM menus
WHERE code = 'ERP_SHIPPING_WAREHOUSE_DAILY';

DROP TABLE IF EXISTS `shipping_warehouse_daily_stock`;
