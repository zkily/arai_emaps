-- 購買・外注管理：親メニュー「支給材管理」を追加し、外注管理配下の支給材料系3画面をその配下へ移動
SET NAMES utf8mb4;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_PURCHASE_SUPPLIED_MATERIAL', '支給材管理', m.id, NULL, 'Present', 4
FROM menus m
WHERE m.code = 'ERP_PURCHASE'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_PURCHASE'
SET cfg.name = '支給材管理',
    cfg.parent_id = parent.id,
    cfg.path = NULL,
    cfg.icon = 'Present',
    cfg.sort_order = 4
WHERE cfg.code = 'ERP_PURCHASE_SUPPLIED_MATERIAL';

UPDATE menus SET sort_order = 5 WHERE code = 'ERP_PURCHASE_SUPPLIES';

UPDATE menus child
INNER JOIN menus new_parent ON new_parent.code = 'ERP_PURCHASE_SUPPLIED_MATERIAL'
SET child.parent_id = new_parent.id,
    child.sort_order = CASE child.code
        WHEN 'ERP_OUTSOURCING_SUPPLIED_STOCK' THEN 1
        WHEN 'ERP_OUTSOURCING_USAGE' THEN 2
        WHEN 'ERP_OUTSOURCING_MATERIAL_ISSUE' THEN 3
    END
WHERE child.code IN (
    'ERP_OUTSOURCING_SUPPLIED_STOCK',
    'ERP_OUTSOURCING_USAGE',
    'ERP_OUTSOURCING_MATERIAL_ISSUE'
);

-- 既に子メニューを見られるロールへ親メニュー権限を付与 + 管理者
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id
  AND c.code IN (
    'ERP_OUTSOURCING_SUPPLIED_STOCK',
    'ERP_OUTSOURCING_USAGE',
    'ERP_OUTSOURCING_MATERIAL_ISSUE'
  )
INNER JOIN menus p ON p.code = 'ERP_PURCHASE_SUPPLIED_MATERIAL';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_PURCHASE_SUPPLIED_MATERIAL';
