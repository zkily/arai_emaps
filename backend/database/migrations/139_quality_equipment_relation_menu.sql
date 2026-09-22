-- 品質管理：親メニュー「設備関係」を追加し、ローラー使用管理をその配下へ移す
SET NAMES utf8mb4;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_QUALITY_EQUIPMENT_RELATION', '設備関係', m.id, NULL, 'Cpu', 3
FROM menus m
WHERE m.code = 'ERP_QUALITY'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_QUALITY'
SET cfg.name = '設備関係',
    cfg.parent_id = parent.id,
    cfg.path = NULL,
    cfg.icon = 'Cpu',
    cfg.sort_order = 3
WHERE cfg.code = 'ERP_QUALITY_EQUIPMENT_RELATION';

UPDATE menus child
INNER JOIN menus new_parent ON new_parent.code = 'ERP_QUALITY_EQUIPMENT_RELATION'
SET child.parent_id = new_parent.id,
    child.sort_order = 1
WHERE child.code = 'ERP_QUALITY_EQUIPMENT';

-- 設備関係の後に来るよう並びを調整
UPDATE menus
SET sort_order = 4
WHERE code = 'ERP_QUALITY_INSPECTION_NEWSPAPER';

-- 既に子メニューを見られるロールへ親メニュー権限を付与 + 管理者
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id
  AND c.code = 'ERP_QUALITY_EQUIPMENT'
INNER JOIN menus p ON p.code = 'ERP_QUALITY_EQUIPMENT_RELATION';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_QUALITY_EQUIPMENT_RELATION';
