-- システム設定配下：ファイル監視器管理（shipping_log アーカイブ等）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order, is_active)
SELECT 'SYSTEM_FILE_WATCHER_MANAGER', 'ファイル監視器管理', p.id, '/system/file-watcher-manager', 'Monitor', 8, 1
FROM menus p
WHERE p.code = 'SYSTEM_SETTINGS'
LIMIT 1;

UPDATE menus cfg
INNER JOIN menus parent ON parent.code = 'SYSTEM_SETTINGS'
SET cfg.name = 'ファイル監視器管理',
    cfg.parent_id = parent.id,
    cfg.path = '/system/file-watcher-manager',
    cfg.icon = 'Monitor',
    cfg.sort_order = 8,
    cfg.is_active = 1
WHERE cfg.code = 'SYSTEM_FILE_WATCHER_MANAGER';

UPDATE menus
SET sort_order = 9
WHERE code = 'SYSTEM_DEVICE_OWNER_QR'
  AND sort_order < 9;

-- 親メニュー権限を持つロールに付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, n.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'SYSTEM_SETTINGS'
INNER JOIN menus n ON n.code = 'SYSTEM_FILE_WATCHER_MANAGER';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, n.id
FROM role_menu_permissions rmp
INNER JOIN menus sibling ON sibling.id = rmp.menu_id AND sibling.code = 'SYSTEM_FILE_WATCHER'
INNER JOIN menus n ON n.code = 'SYSTEM_FILE_WATCHER_MANAGER';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), m.id
FROM menus m
WHERE m.code = 'SYSTEM_FILE_WATCHER_MANAGER';
