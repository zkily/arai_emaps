-- TABLE: schedule_details
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `schedule_details` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `schedule_id` int NOT NULL COMMENT '工単ID',
  `schedule_date` date NOT NULL COMMENT '排産日',
  `planned_qty` int NOT NULL DEFAULT '0' COMMENT '当日計画数量',
  `actual_qty` int NOT NULL DEFAULT '0' COMMENT '実績数量',
  `defect_qty` int NOT NULL DEFAULT '0' COMMENT '日次不良数（stock_transaction_logs 不良同期）',
  `remaining_qty` int NOT NULL DEFAULT '0' COMMENT '差分（planned_qty - actual_qty）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_schedule_date` (`schedule_id`,`schedule_date`),
  KEY `idx_sd_date` (`schedule_date`),
  CONSTRAINT `fk_sd_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='毎日排産明細/甘特図データ';

SET FOREIGN_KEY_CHECKS = 1;
