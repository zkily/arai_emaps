-- TABLE: budget_process_working_days
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `budget_process_working_days` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `year` smallint NOT NULL COMMENT '年',
  `month` tinyint NOT NULL COMMENT '月',
  `process_cd` varchar(50) NOT NULL COMMENT '工程CD',
  `process_name` varchar(100) DEFAULT NULL COMMENT '工程名',
  `working_days` int NOT NULL DEFAULT '0' COMMENT '工程別稼働日数',
  `remark` varchar(255) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_budget_proc_wd_ym_pc` (`year`,`month`,`process_cd`),
  KEY `idx_budget_proc_wd_ym` (`year`,`month`),
  KEY `idx_budget_proc_wd_pc` (`process_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='予算分析用 工程別月次稼働日数';

SET FOREIGN_KEY_CHECKS = 1;
