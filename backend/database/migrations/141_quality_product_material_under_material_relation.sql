-- 品質管理：製品材料照会を親メニュー「材料関係」配下へ移す
SET NAMES utf8mb4;

UPDATE menus child
INNER JOIN menus new_parent ON new_parent.code = 'ERP_QUALITY_MATERIAL_RELATION'
SET child.parent_id = new_parent.id,
    child.sort_order = 4
WHERE child.code = 'ERP_QUALITY_PRODUCT_MATERIAL';

-- このメニューだけを見られるロールへ親メニュー権限を付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id
  AND c.code = 'ERP_QUALITY_PRODUCT_MATERIAL'
INNER JOIN menus p ON p.code = 'ERP_QUALITY_MATERIAL_RELATION';
