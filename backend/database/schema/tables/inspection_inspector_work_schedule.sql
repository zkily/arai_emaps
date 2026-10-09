-- TABLE: inspection_inspector_work_schedule
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inspection_inspector_work_schedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `inspector_user_id` int NOT NULL COMMENT '検査員 users.id',
  `schedule_date` date DEFAULT NULL COMMENT '特定日（最優先）',
  `weekday` tinyint DEFAULT NULL COMMENT '0=月曜..6=日曜（曜日別デフォルト）',
  `scheduled_hours` decimal(4,2) NOT NULL DEFAULT '7.60' COMMENT '所定稼働時間（時間）',
  `work_start_time` time DEFAULT NULL COMMENT '勤務開始（指定日/指定時間）',
  `work_end_time` time DEFAULT NULL COMMENT '勤務終了（指定日/指定時間）',
  `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_insp_schedule_date` (`inspector_user_id`,`schedule_date`),
  UNIQUE KEY `uq_insp_weekday` (`inspector_user_id`,`weekday`),
  KEY `idx_insp_schedule_user` (`inspector_user_id`),
  KEY `idx_insp_schedule_date` (`schedule_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='検査員別所定稼働時間';

SET FOREIGN_KEY_CHECKS = 1;
