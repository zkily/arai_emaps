-- 面取工程 生産管理指標 Excel/CSV 取込用
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `chamfering_production_indicator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `fiscal_year` int NULL DEFAULT NULL COMMENT '年度（ファイル名から）',
  `production_month` date NULL DEFAULT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `source_line` int NULL DEFAULT NULL COMMENT '取込元行番号',
  `source_file` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '取込元ファイル名',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '社内品番',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ライン',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `chamfer_planned_quantity` int NULL DEFAULT NULL COMMENT '面取計画',
  `chamfer_actual_quantity` int NULL DEFAULT NULL COMMENT '面取生産数',
  `chamfer_defect_quantity` int NULL DEFAULT NULL COMMENT '面取不良',
  `sw_planned_quantity` int NULL DEFAULT NULL COMMENT 'SW計画',
  `sw_actual_quantity` int NULL DEFAULT NULL COMMENT 'SW生産数',
  `sw_defect_quantity` int NULL DEFAULT NULL COMMENT 'SW不良',
  `shift_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT 'シフト',
  `overtime_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '残業',
  `setup_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '段取',
  `repair_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '修理',
  `adjustment_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '調整',
  `choco_stop_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT 'チョコ停',
  `break_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '休憩',
  `planned_stop_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '停止時間',
  `available_work_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '作業すべき時間',
  `work_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '作業時間',
  `utilization_rate` decimal(10, 4) NULL DEFAULT NULL COMMENT '稼働率',
  `work_rate` decimal(10, 4) NULL DEFAULT NULL COMMENT '作業率',
  `total_production_qty` int NULL DEFAULT NULL COMMENT '生産総数',
  `efficiency_rate` decimal(10, 2) NULL DEFAULT NULL COMMENT '能率',
  `data_source` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'excel' COMMENT 'データソース excel/csv',
  `external_sync_key` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '行内容ハッシュ（重複防止）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_chamfering_indicator_sync_key` (`external_sync_key`),
  INDEX `idx_chamfering_indicator_day` (`production_day`),
  INDEX `idx_chamfering_indicator_line` (`production_line`),
  INDEX `idx_chamfering_indicator_product_cd` (`product_cd`),
  INDEX `idx_chamfering_indicator_fiscal_year` (`fiscal_year`),
  INDEX `idx_chamfering_indicator_source_file` (`source_file`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '面取工程 生産管理指標' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
