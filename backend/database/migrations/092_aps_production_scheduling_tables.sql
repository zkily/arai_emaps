-- APS 排産スケジューリング用テーブル
-- production_lines / line_capacities / production_schedules / schedule_details

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 生産ライン（設備）マスタ
CREATE TABLE IF NOT EXISTS `production_lines` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_code` VARCHAR(50) NOT NULL COMMENT '産線コード（例：加工06）',
  `default_work_hours` DECIMAL(4,2) NOT NULL DEFAULT 0.00 COMMENT '基準稼働時間（時間）',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_line_code` (`line_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生産ライン基礎情報';

-- 2. 産線日別稼働カレンダー
CREATE TABLE IF NOT EXISTS `line_capacities` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT '産線ID',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `available_hours` DECIMAL(4,2) NOT NULL COMMENT '当日可用稼働時間（時間）',
  `note` VARCHAR(255) NULL DEFAULT NULL COMMENT '備考（休日・検修等）',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_line_date` (`line_id`, `work_date`),
  INDEX `idx_work_date` (`work_date`),
  CONSTRAINT `fk_lc_line` FOREIGN KEY (`line_id`) REFERENCES `production_lines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線日別稼働カレンダー';

-- 3. 排産工単主表
CREATE TABLE IF NOT EXISTS `production_schedules` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT '産線ID',
  `order_no` INT NULL DEFAULT NULL COMMENT '順番',
  `order_id` INT NULL DEFAULT NULL COMMENT '外部注文ID',
  `item_name` VARCHAR(100) NOT NULL COMMENT '品名',
  `material_shortage` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '材料不足フラグ',
  `lot_qty` INT NOT NULL DEFAULT 0 COMMENT '実績生ロット数',
  `planned_process_qty` INT NOT NULL COMMENT '予定加工数量',
  `prev_month_carryover` INT NOT NULL DEFAULT 0 COMMENT '前月繰越',
  `due_date` DATE NULL DEFAULT NULL COMMENT '完成期日',
  `material_date` DATE NULL DEFAULT NULL COMMENT '材料調達日',
  `setup_time` INT NOT NULL DEFAULT 0 COMMENT '段取時間（分）',
  `efficiency` DECIMAL(5,2) NOT NULL DEFAULT 100.00 COMMENT '時間能率（%）',
  `daily_capacity` INT NOT NULL COMMENT '日生産能力',
  `planned_output_qty` INT NOT NULL DEFAULT 0 COMMENT '予定産出数量',
  `start_date` DATE NULL DEFAULT NULL COMMENT '開始期日',
  `end_date` DATE NULL DEFAULT NULL COMMENT '終了期日',
  `completion_rate` DECIMAL(5,2) NULL DEFAULT NULL COMMENT '完成比率（%）',
  `status` VARCHAR(20) NOT NULL DEFAULT 'PLANNING' COMMENT 'PLANNING / IN_PROGRESS / COMPLETED',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_ps_line` (`line_id`),
  INDEX `idx_ps_status` (`status`),
  CONSTRAINT `fk_ps_line` FOREIGN KEY (`line_id`) REFERENCES `production_lines` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産工単主計画表';

-- 4. 毎日排産明細（甘特図データ）
CREATE TABLE IF NOT EXISTS `schedule_details` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `schedule_id` INT NOT NULL COMMENT '工単ID',
  `schedule_date` DATE NOT NULL COMMENT '排産日',
  `planned_qty` INT NOT NULL DEFAULT 0 COMMENT '当日計画数量',
  `actual_qty` INT NOT NULL DEFAULT 0 COMMENT '実績数量',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_schedule_date` (`schedule_id`, `schedule_date`),
  INDEX `idx_sd_date` (`schedule_date`),
  CONSTRAINT `fk_sd_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='毎日排産明細/甘特図データ';

SET FOREIGN_KEY_CHECKS = 1;
