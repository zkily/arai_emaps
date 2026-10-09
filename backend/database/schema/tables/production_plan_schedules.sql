-- TABLE: production_plan_schedules
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_plan_schedules` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) NOT NULL,
  `processed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `machine_name` varchar(100) DEFAULT NULL,
  `product_name` varchar(200) DEFAULT NULL,
  `production_order` varchar(100) DEFAULT NULL,
  `planned_quantity` decimal(18,4) DEFAULT NULL,
  `production_start_date` date DEFAULT NULL,
  `production_end_date` date DEFAULT NULL,
  `actual_production` decimal(18,4) DEFAULT NULL,
  `variance` decimal(18,4) DEFAULT NULL,
  `achievement_rate` decimal(10,2) DEFAULT NULL,
  `total_production_time` decimal(18,2) DEFAULT NULL,
  `operation_variance` varchar(100) DEFAULT NULL,
  `material_lot_count` int DEFAULT NULL,
  `material_name` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pps_file` (`file_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='加工/溶接状況(Excel取込)';

SET FOREIGN_KEY_CHECKS = 1;
