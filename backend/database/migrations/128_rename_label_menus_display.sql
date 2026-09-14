-- メニュー表示名変更：ラベル発行 → 表示発行、テキストラベル印刷 → 各種表示印刷

UPDATE menus
SET name = '表示発行'
WHERE code = 'MASTER_LABEL';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'MASTER_TEXT_LABEL_PRINT', '各種表示印刷', p.id, '/master/text-label-print', 'EditPen', 4, 1
FROM menus p
WHERE p.code = 'MASTER_LABEL'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus label_parent ON label_parent.code = 'MASTER_LABEL'
SET cfg.name = '各種表示印刷',
    cfg.parent_id = label_parent.id,
    cfg.path = '/master/text-label-print',
    cfg.icon = 'EditPen',
    cfg.sort_order = 4,
    cfg.is_active = 1
WHERE cfg.code = 'MASTER_TEXT_LABEL_PRINT';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, n.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'MASTER_LABEL'
INNER JOIN menus n ON n.code = 'MASTER_TEXT_LABEL_PRINT';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), m.id
FROM menus m
WHERE m.code = 'MASTER_TEXT_LABEL_PRINT';
