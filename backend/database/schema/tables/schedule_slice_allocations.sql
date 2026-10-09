-- TABLE: schedule_slice_allocations
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `schedule_slice_allocations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `schedule_id` int NOT NULL COMMENT 'production_schedules.id',
  `work_date` date NOT NULL COMMENT '作業日',
  `period_start` time NOT NULL COMMENT '区間開始（含む）',
  `period_end` time NOT NULL COMMENT '区間終了（含まず）',
  `planned_qty` int NOT NULL DEFAULT '0' COMMENT '当該区間の計画数量',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '同日並び',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ssa_sched_period` (`schedule_id`,`work_date`,`period_start`,`period_end`),
  KEY `idx_ssa_sched_date` (`schedule_id`,`work_date`),
  CONSTRAINT `fk_ssa_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産時間帯別配分';

SET FOREIGN_KEY_CHECKS = 1;
