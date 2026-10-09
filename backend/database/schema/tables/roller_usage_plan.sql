-- TABLE: roller_usage_plan
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `roller_usage_plan` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `plan_month` char(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '対象月 YYYY-MM',
  `planned_exec_date` date NOT NULL COMMENT '予定実施日',
  `planned_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '予定段取品',
  `exec_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ローラー交換' COMMENT '実施内容',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'planned' COMMENT 'planned|done|cancelled',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '同日複数時の並び',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '登録者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_roller_usage_plan_roller_month` (`roller_cd`,`plan_month`),
  KEY `idx_roller_usage_plan_exec_date` (`planned_exec_date`),
  KEY `idx_roller_usage_plan_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラー予定実施スケジュール';

SET FOREIGN_KEY_CHECKS = 1;
