-- 成形工程 生産管理指標 Excel/CSV 取込用
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `forming_production_indicator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `fiscal_year` int NULL DEFAULT NULL COMMENT '年度（ファイル名から）',
  `production_month` date NULL DEFAULT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `source_line` int NULL DEFAULT NULL COMMENT '取込元行番号',
  `source_file` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '取込元ファイル名',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '社内品番',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ライン',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `planned_quantity` int NULL DEFAULT NULL COMMENT '生産計画数',
  `actual_quantity` int NULL DEFAULT NULL COMMENT '生産数',
  `defect_quantity` int NULL DEFAULT NULL COMMENT '不良数',
  `shift_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT 'シフト',
  `overtime_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '残業',
  `setup_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '段取',
  `repair_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '修理',
  `adjustment_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '調整',
  `break_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '休憩',
  `waiting_repair_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '対応待ち（残業中未復旧）',
  `planned_stop_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '停止時間(計画停止)',
  `available_work_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '作業すべき時間',
  `work_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '作業時間',
  `utilization_rate` decimal(10, 4) NULL DEFAULT NULL COMMENT '稼働率',
  `work_rate` decimal(10, 4) NULL DEFAULT NULL COMMENT '作業率',
  `efficiency_rate` decimal(10, 2) NULL DEFAULT NULL COMMENT '能率',
  `setup_adjustment_flag` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '段取・調整',
  `yellow_box_qty` int NULL DEFAULT NULL COMMENT '黄箱品',
  `metric_60` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '列「60」',
  `data_source` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'excel' COMMENT 'データソース excel/csv',
  `external_sync_key` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '行内容ハッシュ（重複防止）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_forming_indicator_sync_key` (`external_sync_key`),
  INDEX `idx_forming_indicator_day` (`production_day`),
  INDEX `idx_forming_indicator_line` (`production_line`),
  INDEX `idx_forming_indicator_product_cd` (`product_cd`),
  INDEX `idx_forming_indicator_fiscal_year` (`fiscal_year`),
  INDEX `idx_forming_indicator_source_file` (`source_file`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '成形工程 生産管理指標' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
