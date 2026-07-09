-- ラベル発行を マスタ管理 直下（マスタ・BOM と同級）へ移動

UPDATE menus child
INNER JOIN menus parent ON parent.code = 'MASTER'
SET child.name = 'ラベル発行',
    child.parent_id = parent.id,
    child.path = NULL,
    child.icon = 'Printer',
    child.sort_order = 3,
    child.is_active = 1
WHERE child.code = 'MASTER_LABEL';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'MASTER_LABEL', 'ラベル発行', m.id, NULL, 'Printer', 3, 1
FROM menus m
WHERE m.code = 'MASTER'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus label_parent ON label_parent.code = 'MASTER_LABEL'
SET cfg.parent_id = label_parent.id,
    cfg.is_active = 1
WHERE cfg.code = 'MASTER_PRODUCT_LABEL_CONFIG';
