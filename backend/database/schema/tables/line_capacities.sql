-- TABLE: line_capacities
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `line_capacities` (
  `id` int NOT NULL AUTO_INCREMENT,
  `line_id` int NOT NULL COMMENT '産線ID',
  `work_date` date NOT NULL COMMENT '作業日',
  `available_hours` decimal(4,2) NOT NULL COMMENT '当日可用稼働時間（時間）',
  `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備考（休日・検修等）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_line_date` (`line_id`,`work_date`),
  KEY `idx_work_date` (`work_date`),
  CONSTRAINT `fk_lc_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線日別稼働カレンダー';

SET FOREIGN_KEY_CHECKS = 1;
