-- SEED: role_operation_permissions
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `role_operation_permissions` (`id`, `role_id`, `module`, `can_create`, `can_edit`, `can_delete`, `can_export`, `can_approve`) VALUES
(1, 1, '販売管理', 1, 1, 1, 1, 1),
(2, 1, '購買管理', 1, 1, 1, 1, 1),
(3, 1, '在庫管理', 1, 1, 1, 1, 1),
(4, 1, '原価・会計', 1, 1, 1, 1, 1),
(5, 1, '生産計画', 1, 1, 1, 1, 1),
(6, 1, '製造実行', 1, 1, 1, 1, 1),
(7, 1, '品質管理', 1, 1, 1, 1, 1),
(8, 2, '販売管理', 1, 1, 0, 1, 0),
(9, 2, '購買管理', 1, 1, 0, 1, 0),
(10, 2, '在庫管理', 1, 1, 0, 1, 0),
(11, 2, '原価・会計', 0, 0, 0, 1, 0),
(12, 2, '生産計画', 1, 1, 0, 1, 0);

SET FOREIGN_KEY_CHECKS = 1;
