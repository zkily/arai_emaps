-- ローラー使用管理: 手動予定スケジュール（roller_cd 単位・月内複数可）
ALTER TABLE `roller_master`
  ADD COLUMN `schedule_mode` VARCHAR(10) NOT NULL DEFAULT 'auto'
    COMMENT 'auto=自動予測, manual=手動予定日' AFTER `machine_cd`;

CREATE TABLE IF NOT EXISTS `roller_usage_plan` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` VARCHAR(50) NOT NULL COMMENT 'ローラーCD',
  `plan_month` CHAR(7) NOT NULL COMMENT '対象月 YYYY-MM',
  `planned_exec_date` DATE NOT NULL COMMENT '予定実施日',
  `planned_product_cd` VARCHAR(50) NULL COMMENT '予定段取品',
  `exec_type` VARCHAR(50) NOT NULL DEFAULT 'ローラー交換' COMMENT '実施内容',
  `status` VARCHAR(20) NOT NULL DEFAULT 'planned' COMMENT 'planned|done|cancelled',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '同日複数時の並び',
  `note` TEXT NULL COMMENT '備考',
  `created_by` VARCHAR(100) NULL COMMENT '登録者',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_roller_usage_plan_roller_month` (`roller_cd`, `plan_month`),
  KEY `idx_roller_usage_plan_exec_date` (`planned_exec_date`),
  KEY `idx_roller_usage_plan_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラー予定実施スケジュール';
