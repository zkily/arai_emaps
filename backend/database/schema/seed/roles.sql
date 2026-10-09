-- SEED: roles
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `roles` (`id`, `name`, `code`, `description`, `is_system`, `is_super_admin`, `data_scope`, `custom_departments`, `is_active`) VALUES
(1, '管理者', 'admin', 'システム管理者（全権限）', 1, 1, 'all', NULL, 1),
(2, '一般ユーザー', 'user', '一般ユーザー（読み書き権限）', 1, 0, 'department', NULL, 1),
(3, '閲覧者', 'viewer', '閲覧のみ', 0, 0, 'department', NULL, 1);

SET FOREIGN_KEY_CHECKS = 1;
