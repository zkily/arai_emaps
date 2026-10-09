-- SEED: organizations
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `organizations` (`id`, `code`, `name`, `type`, `parent_id`, `manager_name`, `location`, `phone`, `email`, `description`, `sort_order`, `is_active`) VALUES
(1, 'COMP001', '株式会社Smart-EMAP', 'company', NULL, NULL, NULL, NULL, NULL, NULL, 1, 1),
(2, 'SITE001', '本社', 'site', 1, NULL, NULL, NULL, NULL, NULL, 1, 1),
(3, 'SITE002', '大阪工場', 'site', 1, NULL, NULL, NULL, NULL, NULL, 2, 1),
(4, 'DEPT001', '営業部', 'department', 2, NULL, NULL, NULL, NULL, NULL, 1, 1),
(5, 'DEPT002', '管理部', 'department', 2, NULL, NULL, NULL, NULL, NULL, 2, 1),
(6, 'DEPT003', '製造部', 'department', 3, NULL, NULL, NULL, NULL, NULL, 1, 1),
(7, 'DEPT004', '品質管理部', 'department', 3, NULL, NULL, NULL, NULL, NULL, 2, 1),
(8, 'LINE001', '第1ライン', 'line', 6, NULL, NULL, NULL, NULL, NULL, 1, 1),
(9, 'LINE002', '第2ライン', 'line', 6, NULL, NULL, NULL, NULL, NULL, 2, 1);

SET FOREIGN_KEY_CHECKS = 1;
