-- 設備日別稼働時間帯テーブル
-- line_capacity_time_slots: 各設備の各日の稼働時間帯を管理
-- 保存時に SUM(end_time - start_time) → line_capacities.available_hours へ反映

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `line_capacity_time_slots` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT '産線ID',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `start_time` TIME NOT NULL COMMENT '開始時刻',
  `end_time` TIME NOT NULL COMMENT '終了時刻',
  `sort_order` SMALLINT NOT NULL DEFAULT 0 COMMENT '表示順',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_lcts_line_date` (`line_id`, `work_date`),
  CONSTRAINT `fk_lcts_line` FOREIGN KEY (`line_id`) REFERENCES `production_lines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備日別稼働時間帯';

SET FOREIGN_KEY_CHECKS = 1;
