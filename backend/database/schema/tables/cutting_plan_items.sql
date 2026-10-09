-- TABLE: cutting_plan_items
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `cutting_plan_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `run_id` int NOT NULL,
  `instruction_plan_id` int DEFAULT NULL,
  `source_management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `planned_quantity` int NOT NULL DEFAULT '0',
  `instruction_production_quantity` int NOT NULL DEFAULT '0' COMMENT '指示計画の生産数',
  `production_lot_size` int DEFAULT NULL,
  `lot_number` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `take_count` int DEFAULT NULL,
  `cutting_length` decimal(10,2) DEFAULT NULL,
  `assigned_machine_id` int DEFAULT NULL,
  `assigned_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sequence_no` int NOT NULL DEFAULT '0',
  `planned_day` date DEFAULT NULL,
  `planned_start` datetime DEFAULT NULL,
  `planned_end` datetime DEFAULT NULL,
  `estimated_minutes` decimal(10,2) NOT NULL DEFAULT '0.00',
  `efficiency_rate` decimal(10,2) DEFAULT NULL,
  `setup_time_min` int DEFAULT NULL,
  `is_locked` tinyint(1) NOT NULL DEFAULT '0',
  `publish_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PLANNED',
  `published_cutting_id` int DEFAULT NULL,
  `actual_quantity` int NOT NULL DEFAULT '0',
  `completion_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PLANNED',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_cutting_plan_items_run` (`run_id`),
  KEY `idx_cutting_plan_items_machine_seq` (`run_id`,`assigned_machine_id`,`sequence_no`),
  KEY `idx_cutting_plan_items_day` (`run_id`,`planned_day`),
  KEY `idx_cutting_plan_items_instruction` (`instruction_plan_id`),
  KEY `idx_cutting_plan_items_management_code` (`source_management_code`),
  KEY `idx_cutting_plan_items_published_cutting` (`published_cutting_id`),
  CONSTRAINT `fk_cutting_plan_items_run` FOREIGN KEY (`run_id`) REFERENCES `cutting_plan_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='切断計画明細';

SET FOREIGN_KEY_CHECKS = 1;
