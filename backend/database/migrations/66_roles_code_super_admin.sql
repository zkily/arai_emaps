-- 路线 B: roles.code + is_super_admin（RBAC 正規化）
ALTER TABLE roles
  ADD COLUMN code VARCHAR(50) NULL COMMENT 'ロールコード（users.role 同期・英数字）' AFTER name,
  ADD COLUMN is_super_admin TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'システム管理者（全権限）' AFTER is_system;

UPDATE roles SET code = 'admin', is_super_admin = 1 WHERE name = '管理者';
UPDATE roles SET code = 'user', is_super_admin = 0 WHERE name = '一般ユーザー';
UPDATE roles SET code = 'viewer', is_super_admin = 0 WHERE name = '閲覧者';
UPDATE roles SET code = 'manager', is_super_admin = 0 WHERE name = 'マネージャー';
UPDATE roles SET code = 'worker', is_super_admin = 0 WHERE name = '作業者';
UPDATE roles SET code = 'guest', is_super_admin = 0 WHERE name = 'ゲスト';

UPDATE roles SET code = CONCAT('role_', id) WHERE code IS NULL OR TRIM(code) = '';

CREATE UNIQUE INDEX uk_roles_code ON roles (code);
