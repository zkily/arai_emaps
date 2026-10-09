-- TABLE: production_plan_updates
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_plan_updates` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) NOT NULL COMMENT '来源文件名',
  `processed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `plan_date` date DEFAULT NULL COMMENT '生産日',
  `quantity` decimal(18,4) DEFAULT NULL COMMENT '生産数',
  `machine_name` varchar(100) DEFAULT NULL,
  `machine_cd` varchar(50) DEFAULT NULL,
  `process_name` varchar(50) DEFAULT NULL COMMENT '成型/溶接',
  `operator` varchar(100) DEFAULT NULL COMMENT '生産準',
  `product_name` varchar(200) DEFAULT NULL,
  `product_cd` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ppu_file` (`file_name`),
  KEY `idx_ppu_plan_date` (`plan_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='計画更新(Excel取込)';

SET FOREIGN_KEY_CHECKS = 1;
