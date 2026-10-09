-- SEED: approval_route_steps
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `approval_route_steps` (`id`, `route_id`, `step_order`, `step_name`, `approver_type`, `approver_id`, `approver_position`, `is_optional`) VALUES
(1, 1, 1, '申請者', 'position', NULL, '申請者', 0),
(2, 1, 2, '課長', 'position', NULL, '課長', 0),
(3, 1, 3, '部長', 'position', NULL, '部長', 0);

SET FOREIGN_KEY_CHECKS = 1;
