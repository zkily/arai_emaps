-- 品質管理：親メニュー「通知関係」を追加し、実績工程通知をその配下へ移して「検査通知(防錆)」に改名
SET NAMES utf8mb4;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_QUALITY_NOTIFICATION_RELATION', '通知関係', m.id, NULL, 'Bell', 4
FROM menus m
WHERE m.code = 'ERP_QUALITY'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'ERP_QUALITY'
SET cfg.name = '通知関係',
    cfg.parent_id = parent.id,
    cfg.path = NULL,
    cfg.icon = 'Bell',
    cfg.sort_order = 4
WHERE cfg.code = 'ERP_QUALITY_NOTIFICATION_RELATION';

UPDATE menus child
INNER JOIN menus new_parent ON new_parent.code = 'ERP_QUALITY_NOTIFICATION_RELATION'
SET child.parent_id = new_parent.id,
    child.name = '検査通知(防錆)',
    child.sort_order = 1
WHERE child.code = 'ERP_QUALITY_INSPECTION_NEWSPAPER';

UPDATE notification_settings
SET event_name = '検査通知(防錆)'
WHERE event_code = 'INSPECTION_NEWSPAPER_ALERT';

UPDATE email_templates
SET name = '検査通知(防錆)'
WHERE code = 'INSPECTION_NEWSPAPER_ALERT'
   OR event_code = 'INSPECTION_NEWSPAPER_ALERT';

-- 既に子メニューを見られるロールへ親メニュー権限を付与 + 管理者
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id
  AND c.code = 'ERP_QUALITY_INSPECTION_NEWSPAPER'
INNER JOIN menus p ON p.code = 'ERP_QUALITY_NOTIFICATION_RELATION';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'ERP_QUALITY_NOTIFICATION_RELATION';
