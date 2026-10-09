-- SEED: production_review_capacity
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `production_review_capacity` (`id`, `target_month`, `process_cd`, `process_name`, `equipment_label`, `standard_rate`, `shift_label`, `working_days`, `utilization_rate_pct`, `plan_adjust_rate_pct`, `daily_regular_hours`, `sort_order`) VALUES
(1, '', 'cutting', '切断', '5.5台', 445, '2直', 0, 96.00, 100.00, 8, 1),
(2, '', 'chamfering', '面取', '4.5台 (2工程)', 295, '2直', 0, 96.00, 100.00, 7, 2),
(3, '', 'molding', '成型', '24ライン', 122, '2直', 0, 96.00, 100.00, 4, 3),
(4, '', 'plating', 'メッキ', '1台', 1620, '3直', 0, 96.00, 100.00, 2, 4),
(5, '', 'inspection', '検査', '11人', 540, '2直', 0, 96.00, 100.00, 8, 5),
(6, '', 'welding', '溶接', '6人', 131, '2直', 0, 96.00, 100.00, 5, 6),
(7, '', 'welding_sp', '溶接SP', '2人', 145, '2直', 0, 96.00, 100.00, 2, 7);

SET FOREIGN_KEY_CHECKS = 1;
