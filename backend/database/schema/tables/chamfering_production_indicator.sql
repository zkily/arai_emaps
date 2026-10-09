-- TABLE: chamfering_production_indicator
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `chamfering_production_indicator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `fiscal_year` int DEFAULT NULL COMMENT '年度（ファイル名から）',
  `production_month` date DEFAULT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `source_line` int DEFAULT NULL COMMENT '取込元行番号',
  `source_file` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '取込元ファイル名',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '社内品番',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ライン',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品名',
  `chamfer_planned_quantity` int DEFAULT NULL COMMENT '面取計画',
  `chamfer_actual_quantity` int DEFAULT NULL COMMENT '面取生産数',
  `chamfer_defect_quantity` int DEFAULT NULL COMMENT '面取不良',
  `sw_planned_quantity` int DEFAULT NULL COMMENT 'SW計画',
  `sw_actual_quantity` int DEFAULT NULL COMMENT 'SW生産数',
  `sw_defect_quantity` int DEFAULT NULL COMMENT 'SW不良',
  `shift_hours` decimal(10,3) DEFAULT NULL COMMENT 'シフト',
  `overtime_hours` decimal(10,3) DEFAULT NULL COMMENT '残業',
  `setup_hours` decimal(10,3) DEFAULT NULL COMMENT '段取',
  `repair_hours` decimal(10,3) DEFAULT NULL COMMENT '修理',
  `adjustment_hours` decimal(10,3) DEFAULT NULL COMMENT '調整',
  `choco_stop_hours` decimal(10,3) DEFAULT NULL COMMENT 'チョコ停',
  `break_hours` decimal(10,3) DEFAULT NULL COMMENT '休憩',
  `planned_stop_hours` decimal(10,3) DEFAULT NULL COMMENT '停止時間',
  `available_work_hours` decimal(10,3) DEFAULT NULL COMMENT '作業すべき時間',
  `work_hours` decimal(10,3) DEFAULT NULL COMMENT '作業時間',
  `utilization_rate` decimal(10,4) DEFAULT NULL COMMENT '稼働率',
  `work_rate` decimal(10,4) DEFAULT NULL COMMENT '作業率',
  `total_production_qty` int DEFAULT NULL COMMENT '生産総数',
  `efficiency_rate` decimal(10,2) DEFAULT NULL COMMENT '能率',
  `data_source` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'excel' COMMENT 'データソース excel/csv',
  `external_sync_key` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '行内容ハッシュ（重複防止）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_chamfering_indicator_sync_key` (`external_sync_key`),
  KEY `idx_chamfering_indicator_day` (`production_day`),
  KEY `idx_chamfering_indicator_line` (`production_line`),
  KEY `idx_chamfering_indicator_product_cd` (`product_cd`),
  KEY `idx_chamfering_indicator_fiscal_year` (`fiscal_year`),
  KEY `idx_chamfering_indicator_source_file` (`source_file`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='面取工程 生産管理指標';

SET FOREIGN_KEY_CHECKS = 1;
