-- メッキ工程 生産管理指標 Excel/CSV 取込用（日次集計）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `plating_production_indicator` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `fiscal_year` int NULL DEFAULT NULL COMMENT '年度（ファイル名から）',
  `production_month` date NULL DEFAULT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `source_line` int NULL DEFAULT NULL COMMENT '取込元行番号',
  `source_file` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '取込元ファイル名',
  `planned_quantity` int NULL DEFAULT NULL COMMENT '計画数',
  `actual_quantity` int NULL DEFAULT NULL COMMENT '実績数',
  `defect_quantity` int NULL DEFAULT NULL COMMENT '不良数',
  `defect_plating_scratch` int NULL DEFAULT NULL COMMENT 'メッキ後キズ',
  `defect_moya_kaburi` int NULL DEFAULT NULL COMMENT 'モヤ/カブリ',
  `defect_nickel` int NULL DEFAULT NULL COMMENT 'ニッケル',
  `defect_contact` int NULL DEFAULT NULL COMMENT '接触',
  `defect_other` int NULL DEFAULT NULL COMMENT 'メ他',
  `shift_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT 'シフト',
  `maintenance_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT 'メンテ時間',
  `trouble_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT 'トラブル時間',
  `choco_stop_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT 'チョコ停',
  `planned_stop_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '計画停止（在庫など）',
  `available_work_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '作業すべき時間',
  `work_hours` decimal(10, 3) NULL DEFAULT NULL COMMENT '作業時間（入槽時間）',
  `work_rate` decimal(10, 4) NULL DEFAULT NULL COMMENT '作業率',
  `utilization_rate` decimal(10, 4) NULL DEFAULT NULL COMMENT '稼働率',
  `total_inspection_qty` int NULL DEFAULT NULL COMMENT '検査総数',
  `efficiency_rate` decimal(10, 2) NULL DEFAULT NULL COMMENT '能率',
  `data_source` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'excel' COMMENT 'データソース excel/csv',
  `external_sync_key` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '行内容ハッシュ（重複防止）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_plating_indicator_sync_key` (`external_sync_key`),
  INDEX `idx_plating_indicator_day` (`production_day`),
  INDEX `idx_plating_indicator_fiscal_year` (`fiscal_year`),
  INDEX `idx_plating_indicator_source_file` (`source_file`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'メッキ工程 生産管理指標（日次）' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
