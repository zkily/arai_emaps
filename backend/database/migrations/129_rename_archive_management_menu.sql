-- メニュー表示名変更：データベースファイル管理 → アーカイブ管理

UPDATE menus
SET name = 'アーカイブ管理'
WHERE code = 'SYSTEM_FILE_WATCHER_MANAGER';
