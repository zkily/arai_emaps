-- 生産計画 Excel 取込用テーブル（監視ファイル 加工計画/溶接計画 用）
-- production_plan_updates: 計画更新
-- production_plan_schedules: 加工状況/溶接状況
-- production_plan_rate: 操業度

DROP TABLE IF EXISTS `production_plan_rate`;
DROP TABLE IF EXISTS `production_plan_schedules`;
DROP TABLE IF EXISTS `production_plan_updates`;

CREATE TABLE `production_plan_updates` (
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

CREATE TABLE `production_plan_schedules` (
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

CREATE TABLE `production_plan_rate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) NOT NULL,
  `processed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `machine_cd` varchar(50) DEFAULT NULL,
  `machine_name` varchar(100) DEFAULT NULL,
  `operation_variance` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ppr_file` (`file_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='操業度(Excel取込)';
