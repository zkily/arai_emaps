-- TABLE: line_capacity_time_slots
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `line_capacity_time_slots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `line_id` int NOT NULL COMMENT '産線ID',
  `work_date` date NOT NULL COMMENT '作業日',
  `start_time` time NOT NULL COMMENT '開始時刻',
  `end_time` time NOT NULL COMMENT '終了時刻',
  `sort_order` smallint NOT NULL DEFAULT '0' COMMENT '表示順',
  `is_rest` tinyint(1) NOT NULL DEFAULT '0' COMMENT '1=休憩（稼働から除く）',
  `slot_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'work' COMMENT 'work=稼働 / rest=休憩 / tech=技術使用 / maintenance=保全',
  `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用途メモ（例: 技術部トライ）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_lcts_line_date` (`line_id`,`work_date`),
  CONSTRAINT `fk_lcts_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備日別稼働時間帯';

SET FOREIGN_KEY_CHECKS = 1;
