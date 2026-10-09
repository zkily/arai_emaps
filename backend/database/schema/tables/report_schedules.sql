-- TABLE: report_schedules
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `report_schedules` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `report_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'レポートコード',
  `schedule_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'daily' COMMENT 'daily|weekly|monthly',
  `schedule_time` time NOT NULL DEFAULT '08:00:00' COMMENT '実行時刻（JST）',
  `schedule_config` json DEFAULT NULL COMMENT '曜日・実行日などの詳細',
  `parameters` json DEFAULT NULL COMMENT '既定パラメータ（相対日付表現を含む）',
  `format` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '出力形式の上書き',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '有効フラグ',
  `last_run_at` datetime DEFAULT NULL COMMENT '最終実行日時',
  `next_run_at` datetime DEFAULT NULL COMMENT '次回実行予定',
  `created_by` int DEFAULT NULL COMMENT '作成者 users.id',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_report_schedules_code` (`report_code`),
  KEY `idx_report_schedules_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='レポートスケジュール';

SET FOREIGN_KEY_CHECKS = 1;
