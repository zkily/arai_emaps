-- ============================================================
-- システム管理テーブル作成 (MySQL)
-- 組織、ロール、権限、メニュー管理
-- ============================================================

-- ========== 組織テーブル ==========
CREATE TABLE IF NOT EXISTS organizations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '組織コード（一意）',
    name VARCHAR(200) NOT NULL COMMENT '組織名',
    type VARCHAR(20) NOT NULL COMMENT '種類（company:会社, site:拠点, department:部門, line:ライン）',
    parent_id INT NULL COMMENT '親組織ID',
    manager_name VARCHAR(100) NULL COMMENT '責任者名',
    location VARCHAR(200) NULL COMMENT '所在地',
    phone VARCHAR(50) NULL COMMENT '電話番号',
    email VARCHAR(100) NULL COMMENT 'メールアドレス',
    description TEXT NULL COMMENT '説明',
    sort_order INT DEFAULT 0 COMMENT '表示順序',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_organizations_parent (parent_id),
    INDEX idx_organizations_type (type),
    CONSTRAINT fk_organizations_parent FOREIGN KEY (parent_id) REFERENCES organizations(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='組織テーブル（会社、拠点、部門、ライン）';


-- ========== ロールテーブル ==========
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT 'ロール名',
    description TEXT NULL COMMENT '説明',
    is_system TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'システムロールフラグ（1:削除不可）',
    data_scope VARCHAR(20) NOT NULL DEFAULT 'department' COMMENT 'データ参照範囲（self/department/department_below/all/custom）',
    custom_departments JSON NULL COMMENT 'カスタム部門リスト（data_scope=customの場合）',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ロールテーブル';


-- ========== メニューテーブル ==========
CREATE TABLE IF NOT EXISTS menus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'メニューコード',
    name VARCHAR(100) NOT NULL COMMENT 'メニュー名',
    parent_id INT NULL COMMENT '親メニューID',
    path VARCHAR(200) NULL COMMENT 'ルートパス',
    icon VARCHAR(50) NULL COMMENT 'アイコン名',
    sort_order INT DEFAULT 0 COMMENT '表示順序',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_menus_parent (parent_id),
    CONSTRAINT fk_menus_parent FOREIGN KEY (parent_id) REFERENCES menus(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='メニューテーブル';


-- ========== ロール・メニュー権限関連テーブル ==========
CREATE TABLE IF NOT EXISTS role_menu_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL COMMENT 'ロールID',
    menu_id INT NOT NULL COMMENT 'メニューID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    UNIQUE KEY uk_role_menu (role_id, menu_id),
    INDEX idx_role_menu_permissions_role (role_id),
    INDEX idx_role_menu_permissions_menu (menu_id),
    CONSTRAINT fk_rmp_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_rmp_menu FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ロール・メニュー権限関連テーブル';


-- ========== ロール・操作権限テーブル ==========
CREATE TABLE IF NOT EXISTS role_operation_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL COMMENT 'ロールID',
    module VARCHAR(100) NOT NULL COMMENT 'モジュール名',
    can_create TINYINT(1) DEFAULT 0 COMMENT '新規作成権限',
    can_edit TINYINT(1) DEFAULT 0 COMMENT '編集権限',
    can_delete TINYINT(1) DEFAULT 0 COMMENT '削除権限',
    can_export TINYINT(1) DEFAULT 0 COMMENT '出力権限',
    can_approve TINYINT(1) DEFAULT 0 COMMENT '承認権限',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    UNIQUE KEY uk_role_module (role_id, module),
    INDEX idx_rop_role (role_id),
    CONSTRAINT fk_rop_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ロール・操作権限テーブル';


-- ========== ユーザー・ロール関連テーブル ==========
CREATE TABLE IF NOT EXISTS user_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT 'ユーザーID',
    role_id INT NOT NULL COMMENT 'ロールID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    UNIQUE KEY uk_user_role (user_id, role_id),
    INDEX idx_user_roles_user (user_id),
    INDEX idx_user_roles_role (role_id),
    CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザー・ロール関連テーブル';


-- ========== ユーザーテーブル拡張（カラムが無い場合のみ追加） ==========
DELIMITER //
DROP PROCEDURE IF EXISTS add_system_user_columns//
CREATE PROCEDURE add_system_user_columns()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'department_id') = 0 THEN
    ALTER TABLE users ADD COLUMN department_id INT NULL COMMENT '所属部門ID';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'two_factor_enabled') = 0 THEN
    ALTER TABLE users ADD COLUMN two_factor_enabled TINYINT(1) DEFAULT 0 COMMENT '二要素認証有効フラグ';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'last_login_at') = 0 THEN
    ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP NULL COMMENT '最終ログイン日時';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'status') = 0 THEN
    ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active' COMMENT 'ステータス（active/locked/inactive）';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'idx_users_department') = 0 THEN
    ALTER TABLE users ADD INDEX idx_users_department (department_id);
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'idx_users_status') = 0 THEN
    ALTER TABLE users ADD INDEX idx_users_status (status);
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND CONSTRAINT_NAME = 'fk_users_department') = 0 THEN
    ALTER TABLE users ADD CONSTRAINT fk_users_department FOREIGN KEY (department_id) REFERENCES organizations(id) ON DELETE SET NULL;
  END IF;
END//
DELIMITER ;
CALL add_system_user_columns();
DROP PROCEDURE add_system_user_columns;


-- ========== 初期データ投入 ==========

-- デフォルト組織
INSERT INTO organizations (code, name, type, parent_id, sort_order) VALUES
('COMP001', '株式会社Smart-EMAP', 'company', NULL, 1)
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'SITE001', '本社', 'site', id, 1 FROM organizations WHERE code = 'COMP001' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'SITE002', '大阪工場', 'site', id, 2 FROM organizations WHERE code = 'COMP001' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'DEPT001', '営業部', 'department', id, 1 FROM organizations WHERE code = 'SITE001' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'DEPT002', '管理部', 'department', id, 2 FROM organizations WHERE code = 'SITE001' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'DEPT003', '製造部', 'department', id, 1 FROM organizations WHERE code = 'SITE002' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'DEPT004', '品質管理部', 'department', id, 2 FROM organizations WHERE code = 'SITE002' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'LINE001', '第1ライン', 'line', id, 1 FROM organizations WHERE code = 'DEPT003' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'LINE002', '第2ライン', 'line', id, 2 FROM organizations WHERE code = 'DEPT003' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);


-- デフォルトロール
INSERT INTO roles (name, description, is_system, data_scope) VALUES
('管理者', 'システム管理者（全権限）', 1, 'all'),
('一般ユーザー', '一般ユーザー（読み書き権限）', 1, 'department'),
('閲覧者', '閲覧のみ', 0, 'department')
ON DUPLICATE KEY UPDATE description = VALUES(description);


-- デフォルトメニュー（INSERT IGNORE で重複時はスキップ）
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order) VALUES
('SYSTEM', 'システム管理', NULL, '/system', 'Setting', 1),
('ERP', 'ERP', NULL, '/erp', 'Management', 2),
('APS', 'APS', NULL, '/aps', 'DataAnalysis', 3),
('MES', 'MES', NULL, '/mes', 'Monitor', 4);

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'SYSTEM_USER', 'ユーザー管理', m.id, '/system/users', 'User', 1 FROM menus m WHERE m.code = 'SYSTEM' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'SYSTEM_ORG', '組織管理', m.id, '/system/organization', 'OfficeBuilding', 2 FROM menus m WHERE m.code = 'SYSTEM' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'SYSTEM_ROLE', '権限管理', m.id, '/system/roles', 'Lock', 3 FROM menus m WHERE m.code = 'SYSTEM' LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_SALES', '販売管理', m.id, '/erp/sales', 'Sell', 1 FROM menus m WHERE m.code = 'ERP' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_PURCHASE', '購買管理', m.id, '/erp/purchase', 'ShoppingCart', 2 FROM menus m WHERE m.code = 'ERP' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_INVENTORY', '在庫管理', m.id, '/erp/inventory', 'Box', 3 FROM menus m WHERE m.code = 'ERP' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_COSTING', '原価・会計', m.id, '/erp/costing', 'Coin', 4 FROM menus m WHERE m.code = 'ERP' LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_PLANNING', '生産計画', m.id, '/aps/planning', 'Calendar', 1 FROM menus m WHERE m.code = 'APS' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_SCHEDULING', 'スケジューリング', m.id, '/aps/scheduling', 'Timer', 2 FROM menus m WHERE m.code = 'APS' LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_EXECUTION', '製造実行', m.id, '/mes/execution', 'Operation', 1 FROM menus m WHERE m.code = 'MES' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_QUALITY', '品質管理', m.id, '/mes/quality', 'DocumentChecked', 2 FROM menus m WHERE m.code = 'MES' LIMIT 1;


-- 管理者ロールに全メニュー権限を付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id FROM menus;


-- 管理者ロールに全操作権限を付与
INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '販売管理', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '購買管理', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '在庫管理', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '原価・会計', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '生産計画', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '製造実行', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '品質管理', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;


-- 一般ユーザーロールにERP/APS/MESメニュー権限を付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), id FROM menus
WHERE code LIKE 'ERP%' OR code LIKE 'APS%' OR code LIKE 'MES%';


-- 一般ユーザーロールに操作権限を付与（削除権限なし）
INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '販売管理', 1, 1, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=0, can_export=1, can_approve=0;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '購買管理', 1, 1, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=0, can_export=1, can_approve=0;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '在庫管理', 1, 1, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=0, can_export=1, can_approve=0;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '原価・会計', 0, 0, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=0, can_edit=0, can_delete=0, can_export=1, can_approve=0;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '生産計画', 1, 1, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=0, can_export=1, can_approve=0;
