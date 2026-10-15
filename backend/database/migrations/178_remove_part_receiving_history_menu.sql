-- 部品受入履歴メニュー削除（機能は部品在庫管理(発注・使用)へ統合済み）
SET NAMES utf8mb4;

DELETE rmp
FROM role_menu_permissions rmp
INNER JOIN menus m ON m.id = rmp.menu_id
WHERE m.code = 'ERP_PURCHASE_PART_RECEIVING';

DELETE FROM menus
WHERE code = 'ERP_PURCHASE_PART_RECEIVING';
