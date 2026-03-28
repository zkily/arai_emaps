-- 200: Unified APS schema baseline
-- 适用场景：新库初始化或需要一次性对齐 APS 结构的环境
-- 注意：本脚本为幂等写法；老环境仍可继续按历史迁移逐步执行

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- 1) APS core tables
-- =====================================================================

CREATE TABLE IF NOT EXISTS `line_capacities` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT 'machines.id',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `available_hours` DECIMAL(4,2) NOT NULL COMMENT '当日可用稼働時間（時間）',
  `note` VARCHAR(255) NULL DEFAULT NULL COMMENT '備考',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_line_date` (`line_id`, `work_date`),
  KEY `idx_work_date` (`work_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線日別稼働カレンダー';

CREATE TABLE IF NOT EXISTS `production_schedules` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT 'machines.id',
  `order_no` INT NULL DEFAULT NULL COMMENT '順番',
  `order_id` INT NULL DEFAULT NULL COMMENT '外部注文ID',
  `item_name` VARCHAR(100) NOT NULL COMMENT '品名',
  `product_cd` VARCHAR(50) NULL DEFAULT NULL COMMENT '製品コード',
  `material_shortage` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '材料不足フラグ',
  `lot_qty` INT NOT NULL DEFAULT 0 COMMENT '実績生ロット数',
  `planned_batch_count` INT NOT NULL DEFAULT 0 COMMENT '予定ロット数',
  `lot_size_snapshot` INT NOT NULL DEFAULT 0 COMMENT 'ロットサイズスナップショット',
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
  KEY `idx_ps_line` (`line_id`),
  KEY `idx_ps_status` (`status`),
  KEY `idx_ps_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産工単主計画表';

CREATE TABLE IF NOT EXISTS `schedule_details` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `schedule_id` INT NOT NULL COMMENT 'production_schedules.id',
  `schedule_date` DATE NOT NULL COMMENT '排産日',
  `planned_qty` INT NOT NULL DEFAULT 0 COMMENT '当日計画数量',
  `actual_qty` INT NOT NULL DEFAULT 0 COMMENT '実績数量',
  `remaining_qty` INT NOT NULL DEFAULT 0 COMMENT '差分（planned_qty - actual_qty）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_schedule_date` (`schedule_id`, `schedule_date`),
  KEY `idx_sd_date` (`schedule_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='毎日排産明細';

CREATE TABLE IF NOT EXISTS `line_capacity_time_slots` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT 'machines.id',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `start_time` TIME NOT NULL COMMENT '開始時刻',
  `end_time` TIME NOT NULL COMMENT '終了時刻',
  `sort_order` SMALLINT NOT NULL DEFAULT 0 COMMENT '表示順',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_lcts_line_date` (`line_id`, `work_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備日別稼働時間帯';

CREATE TABLE IF NOT EXISTS `line_product_standard` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT 'machines.id',
  `product_cd` VARCHAR(50) NOT NULL COMMENT '製品コード',
  `std_qty_per_hour` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '小時あたり標準産出量',
  `setup_time_min` INT NOT NULL DEFAULT 0 COMMENT '段取時間（分）',
  `efficiency_pct` DECIMAL(5,2) NOT NULL DEFAULT 100.00 COMMENT '標準能率（%）',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_line_product` (`line_id`, `product_cd`),
  KEY `idx_lps_product` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線×製品標準マスタ';

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
  UNIQUE KEY `uk_ssa_sched_period` (`schedule_id`, `work_date`, `period_start`, `period_end`),
  KEY `idx_ssa_sched_date` (`schedule_id`, `work_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産時間帯別配分';

CREATE TABLE IF NOT EXISTS `aps_batch_plans` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `aps_schedule_id` INT NOT NULL COMMENT 'APS production_schedules.id',
  `production_month` DATE NOT NULL COMMENT '生産月（YYYY-MM-01）',
  `production_line` VARCHAR(50) NOT NULL COMMENT 'ライン（管理コード用）',
  `priority_order` INT NULL DEFAULT NULL COMMENT '順位（APS order_no）',
  `product_cd` VARCHAR(50) NOT NULL COMMENT '製品CD',
  `product_name` VARCHAR(255) NOT NULL COMMENT '製品名',
  `planned_quantity` INT NOT NULL DEFAULT 0 COMMENT 'このバッチで計画する本数（エンジン再計算で変動しうる）',
  `original_planned_quantity` INT NULL DEFAULT NULL COMMENT '計画一覧確定時のロット本数（生産進捗の計画数表示用）',
  `production_lot_size` INT NOT NULL DEFAULT 0 COMMENT '総バッチ数',
  `lot_number` VARCHAR(100) NOT NULL COMMENT 'ロットNo',
  `start_date` DATETIME NULL DEFAULT NULL COMMENT '開始日時',
  `end_date` DATETIME NULL DEFAULT NULL COMMENT '終了日時',
  `status` VARCHAR(20) NOT NULL DEFAULT 'PLANNED' COMMENT '状態',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_aps_schedule_id_lot_number` (`aps_schedule_id`, `lot_number`),
  KEY `idx_aps_schedule_id` (`aps_schedule_id`),
  KEY `idx_production_month` (`production_month`),
  KEY `idx_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='APS バッチ計画';

-- =====================================================================
-- 2) Missing columns on existing tables (idempotent)
-- =====================================================================

SET @dbname = DATABASE();

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'instruction_plans' AND COLUMN_NAME = 'aps_batch_plan_id'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `instruction_plans` ADD COLUMN `aps_batch_plan_id` INT NULL DEFAULT NULL COMMENT ''APS 批次計画参照''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'instruction_plans' AND COLUMN_NAME = 'release_cancelled_at'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `instruction_plans` ADD COLUMN `release_cancelled_at` DATETIME NULL DEFAULT NULL COMMENT ''上游指示撤回日時''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'instruction_plans' AND COLUMN_NAME = 'release_cancel_reason'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `instruction_plans` ADD COLUMN `release_cancel_reason` VARCHAR(255) NULL DEFAULT NULL COMMENT ''上游指示撤回理由''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'instruction_plans' AND COLUMN_NAME = 'release_cancel_by'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `instruction_plans` ADD COLUMN `release_cancel_by` VARCHAR(64) NULL DEFAULT NULL COMMENT ''上游指示撤回者''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'aps_batch_plans' AND COLUMN_NAME = 'original_planned_quantity'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `aps_batch_plans` ADD COLUMN `original_planned_quantity` INT NULL DEFAULT NULL COMMENT ''計画一覧確定時のロット本数（生産進捗の計画数表示用）'' AFTER `planned_quantity`',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE `aps_batch_plans`
SET `original_planned_quantity` = `planned_quantity`
WHERE `original_planned_quantity` IS NULL;

-- =====================================================================
-- 3) Foreign keys (drop/create safely)
-- =====================================================================

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'line_capacities' AND CONSTRAINT_NAME = 'fk_lc_machine'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `line_capacities` ADD CONSTRAINT `fk_lc_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'production_schedules' AND CONSTRAINT_NAME = 'fk_ps_machine'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `production_schedules` ADD CONSTRAINT `fk_ps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'schedule_details' AND CONSTRAINT_NAME = 'fk_sd_schedule'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `schedule_details` ADD CONSTRAINT `fk_sd_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'line_capacity_time_slots' AND CONSTRAINT_NAME = 'fk_lcts_machine'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `line_capacity_time_slots` ADD CONSTRAINT `fk_lcts_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'line_product_standard' AND CONSTRAINT_NAME = 'fk_lps_machine'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `line_product_standard` ADD CONSTRAINT `fk_lps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'schedule_slice_allocations' AND CONSTRAINT_NAME = 'fk_ssa_schedule'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `schedule_slice_allocations` ADD CONSTRAINT `fk_ssa_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- =====================================================================
-- 4) Triggers
-- =====================================================================

DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bi`;
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bu`;

DELIMITER $$
CREATE TRIGGER `tg_schedule_details_remaining_bi`
BEFORE INSERT ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = GREATEST(COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0), 0);
END$$

CREATE TRIGGER `tg_schedule_details_remaining_bu`
BEFORE UPDATE ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = GREATEST(COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0), 0);
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ai`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_au`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ad`;

DELIMITER $$
CREATE TRIGGER `tg_stl_sync_schedule_details_ai`
AFTER INSERT ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF NEW.transaction_time IS NOT NULL
       AND NEW.machine_cd IS NOT NULL
       AND NEW.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(NEW.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_au`
AFTER UPDATE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF OLD.transaction_time IS NOT NULL
       AND OLD.machine_cd IS NOT NULL
       AND OLD.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(OLD.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;

    IF NEW.transaction_time IS NOT NULL
       AND NEW.machine_cd IS NOT NULL
       AND NEW.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(NEW.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_ad`
AFTER DELETE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF OLD.transaction_time IS NOT NULL
       AND OLD.machine_cd IS NOT NULL
       AND OLD.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(OLD.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;
END$$
DELIMITER ;

-- =====================================================================
-- 5) Data correction
-- =====================================================================

UPDATE schedule_details
SET remaining_qty = GREATEST(COALESCE(planned_qty, 0) - COALESCE(actual_qty, 0), 0);

SET FOREIGN_KEY_CHECKS = 1;
