-- TABLE: production_review_capacity
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_review_capacity` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `target_month` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '対象月 YYYY-MM（空=デフォルト）',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程コード',
  `process_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程名',
  `equipment_label` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '設備・人員表示',
  `standard_rate` int NOT NULL DEFAULT '0' COMMENT '標準能率 本/H',
  `shift_label` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '標準稼働直',
  `working_days` int NOT NULL DEFAULT '0' COMMENT '稼働日数（0=対象月カレンダー）',
  `utilization_rate_pct` decimal(5,2) NOT NULL DEFAULT '96.00' COMMENT '稼働率(%) 定時H計算用',
  `plan_adjust_rate_pct` decimal(8,2) NOT NULL DEFAULT '100.00' COMMENT '計画調整率(%) 計画(千本)×調整率',
  `daily_regular_hours` int NOT NULL DEFAULT '0' COMMENT '日当たり定時H',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '表示順',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_prc_month_process` (`target_month`,`process_cd`),
  KEY `idx_prc_target_month` (`target_month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='生産検討会用工程能力';

SET FOREIGN_KEY_CHECKS = 1;
