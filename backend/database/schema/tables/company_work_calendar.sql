-- TABLE: company_work_calendar
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `company_work_calendar` (
  `id` int NOT NULL AUTO_INCREMENT,
  `calendar_date` date NOT NULL COMMENT '日付',
  `day_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'company_holiday' COMMENT 'workday|weekend|national_holiday|company_holiday|paid_leave|extra_workday',
  `is_scheduled` tinyint(1) NOT NULL DEFAULT '0' COMMENT '1=通常稼働日（分母に含む）',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '祝日名・理由等',
  `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_company_work_calendar_date` (`calendar_date`),
  KEY `idx_company_work_calendar_scheduled` (`calendar_date`,`is_scheduled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会社共通稼働カレンダー';

SET FOREIGN_KEY_CHECKS = 1;
