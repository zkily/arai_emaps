-- TABLE: cutting_plan_slices
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `cutting_plan_slices` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `run_id` int NOT NULL,
  `item_id` bigint NOT NULL,
  `machine_id` int DEFAULT NULL,
  `assigned_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `work_date` date NOT NULL,
  `period_start` time NOT NULL,
  `period_end` time NOT NULL,
  `planned_qty` int NOT NULL DEFAULT '0',
  `sort_order` int NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_cutting_plan_slices_run_day` (`run_id`,`work_date`),
  KEY `idx_cutting_plan_slices_item` (`item_id`),
  KEY `idx_cutting_plan_slices_machine` (`machine_id`,`work_date`),
  CONSTRAINT `fk_cutting_plan_slices_item` FOREIGN KEY (`item_id`) REFERENCES `cutting_plan_items` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cutting_plan_slices_run` FOREIGN KEY (`run_id`) REFERENCES `cutting_plan_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='切断計画時間帯スライス';

SET FOREIGN_KEY_CHECKS = 1;
