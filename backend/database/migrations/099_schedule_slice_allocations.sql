-- 排産：日×時間帯ごとの計画数量（ガント時間別用）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `schedule_slice_allocations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `schedule_id` INT NOT NULL COMMENT 'production_schedules.id',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `period_start` TIME NOT NULL COMMENT '区間開始（含む）',
  `period_end` TIME NOT NULL COMMENT '区間終了（含まず）',
  `planned_qty` INT NOT NULL DEFAULT 0 COMMENT '当該区間の計画数量',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '同日並び',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ssa_sched_date` (`schedule_id`, `work_date`),
  UNIQUE KEY `uk_ssa_sched_period` (`schedule_id`, `work_date`, `period_start`, `period_end`),
  CONSTRAINT `fk_ssa_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産時間帯別配分';
