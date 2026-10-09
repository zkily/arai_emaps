-- TABLE: production_plan_rate
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_plan_rate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) NOT NULL,
  `processed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `machine_cd` varchar(50) DEFAULT NULL,
  `machine_name` varchar(100) DEFAULT NULL,
  `operation_variance` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ppr_file` (`file_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='操業度(Excel取込)';

SET FOREIGN_KEY_CHECKS = 1;
