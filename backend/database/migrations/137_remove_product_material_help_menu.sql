-- 製品材料照会 操作説明メニュー削除
SET NAMES utf8mb4;

DELETE rmp
FROM role_menu_permissions rmp
INNER JOIN menus m ON m.id = rmp.menu_id
WHERE m.code = 'ERP_QUALITY_PRODUCT_MATERIAL_HELP';

DELETE FROM menus
WHERE code = 'ERP_QUALITY_PRODUCT_MATERIAL_HELP';
