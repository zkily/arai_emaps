-- SEED: workflow_definitions
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `workflow_definitions` (`id`, `code`, `name`, `document_type`, `approval_route_id`, `timeout_days`, `escalation_enabled`, `escalation_days`, `escalation_target`, `auto_approve_enabled`, `auto_approve_condition`, `is_active`) VALUES
(1, 'WF_PO', '購買発注承認', '発注書', NULL, 3, 1, NULL, NULL, 0, NULL, 1),
(2, 'WF_SO', '受注承認', '受注書', NULL, 2, 1, NULL, NULL, 0, NULL, 1),
(3, 'WF_QT', '見積承認', '見積書', NULL, 1, 0, NULL, NULL, 0, NULL, 1),
(4, 'WF_INV', '請求書承認', '請求書', NULL, 5, 1, NULL, NULL, 0, NULL, 1);

SET FOREIGN_KEY_CHECKS = 1;
