-- 検査員別所定稼働時間（MES 検査稼働率分析用）
-- schedule_date（特定日）> weekday（曜日別）> デフォルト 7.6h

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `inspection_inspector_work_schedule` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `inspector_user_id` INT NOT NULL COMMENT '検査員 users.id',
  `schedule_date` DATE NULL COMMENT '特定日（最優先）',
  `weekday` TINYINT NULL COMMENT '0=月曜..6=日曜（曜日別デフォルト）',
  `scheduled_hours` DECIMAL(4,2) NOT NULL DEFAULT 7.60 COMMENT '所定稼働時間（時間）',
  `note` VARCHAR(255) NULL COMMENT '備考',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_insp_schedule_date` (`inspector_user_id`, `schedule_date`),
  UNIQUE KEY `uq_insp_weekday` (`inspector_user_id`, `weekday`),
  KEY `idx_insp_schedule_user` (`inspector_user_id`),
  KEY `idx_insp_schedule_date` (`schedule_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='検査員別所定稼働時間';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MASTER_INSPECTION_INSPECTOR_WORK_SCHEDULE', '検査員所定工時', m.id, '/master/inspection-inspector-work-schedule', 'Clock', 13
FROM menus m
WHERE m.code = 'MASTER_LIST'
LIMIT 1;

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'MASTER_INSPECTION_INSPECTOR_WORK_SCHEDULE';
