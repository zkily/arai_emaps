-- SEED: approval_routes
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `approval_routes` (`id`, `name`, `type`, `condition_type`, `condition_value`, `condition_min`, `condition_max`, `condition_department_id`, `priority`, `is_active`) VALUES
(1, '通常購買承認', 'amount', NULL, '10万円未満', NULL, 100000.00, NULL, 1, 1),
(2, '高額購買承認', 'amount', NULL, '10万円以上100万円未満', 100000.00, 1000000.00, NULL, 2, 1),
(3, '大規模購買承認', 'amount', NULL, '100万円以上', 1000000.00, NULL, NULL, 3, 1);

SET FOREIGN_KEY_CHECKS = 1;
