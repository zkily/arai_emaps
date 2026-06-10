-- 会社共通稼働カレンダー（祝日・有給・会社休・臨時出勤）
-- 未登録日はデフォルト: 月〜金=通常稼働日、土日=非稼働

CREATE TABLE IF NOT EXISTS `company_work_calendar` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `calendar_date` DATE NOT NULL COMMENT '日付',
  `day_type` VARCHAR(30) NOT NULL DEFAULT 'company_holiday' COMMENT 'workday|weekend|national_holiday|company_holiday|paid_leave|extra_workday',
  `is_scheduled` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1=通常稼働日（分母に含む）',
  `name` VARCHAR(100) NULL COMMENT '祝日名・理由等',
  `note` VARCHAR(255) NULL COMMENT '備考',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_company_work_calendar_date` (`calendar_date`),
  KEY `idx_company_work_calendar_scheduled` (`calendar_date`, `is_scheduled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会社共通稼働カレンダー';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MASTER_COMPANY_WORK_CALENDAR', '会社稼働カレンダー', m.id, '/master/company-work-calendar', 'Calendar', 12
FROM menus m
WHERE m.code = 'MASTER_LIST'
LIMIT 1;

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'MASTER_COMPANY_WORK_CALENDAR';
