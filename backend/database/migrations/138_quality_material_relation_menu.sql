-- 品質管理：親メニュー「材料関係」を追加し、材料受入履歴・材料公差管理・材料使用取込をその配下へ移す
SET NAMES utf8mb4;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_QUALITY_MATERIAL_RELATION', '材料関係', m.id, NULL, 'Box', 1
FROM menus m
WHERE m.code = 'ERP_QUALITY'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_QUALITY'
SET cfg.name = '材料関係',
    cfg.parent_id = parent.id,
    cfg.path = NULL,
    cfg.icon = 'Box',
    cfg.sort_order = 1
WHERE cfg.code = 'ERP_QUALITY_MATERIAL_RELATION';

UPDATE menus child
INNER JOIN menus new_parent ON new_parent.code = 'ERP_QUALITY_MATERIAL_RELATION'
SET child.parent_id = new_parent.id,
    child.sort_order = CASE child.code
      WHEN 'ERP_QUALITY_MATERIAL' THEN 1
      WHEN 'ERP_QUALITY_MATERIAL_TOLERANCE' THEN 2
      WHEN 'ERP_QUALITY_MATERIAL_CUTTING' THEN 3
      ELSE child.sort_order
    END
WHERE child.code IN (
  'ERP_QUALITY_MATERIAL',
  'ERP_QUALITY_MATERIAL_TOLERANCE',
  'ERP_QUALITY_MATERIAL_CUTTING'
);

-- 既に子メニューを見られるロールへ親メニュー権限を付与 + 管理者
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id
  AND c.code IN (
    'ERP_QUALITY_MATERIAL',
    'ERP_QUALITY_MATERIAL_TOLERANCE',
    'ERP_QUALITY_MATERIAL_CUTTING'
  )
INNER JOIN menus p ON p.code = 'ERP_QUALITY_MATERIAL_RELATION';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_QUALITY_MATERIAL_RELATION';
