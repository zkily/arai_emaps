-- schedule_details に不良数（defect_qty）を追加し、
-- remaining_qty = planned_qty - actual_qty - defect_qty とする（負値可）。
-- 成型不良：transaction_type=不良 かつ process_cd=KT04、TRIM(target_cd)=TRIM(工単.product_cd)、DATE(transaction_time)=schedule_date で quantity を合算。
-- 在庫ログに machine_cd が無くても同期する（実績は従来どおり machine 一致）。

SET NAMES utf8mb4;

SET @dbname = DATABASE();

-- 1) schedule_details に defect_qty
SET @col_exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'schedule_details' AND COLUMN_NAME = 'defect_qty'
);
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE `schedule_details` ADD COLUMN `defect_qty` int NOT NULL DEFAULT 0 COMMENT ''日次不良数（stock_transaction_logs 不良同期）'' AFTER `actual_qty`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2) remaining トリガー（良品・不良を差し引き）
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bi`;
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bu`;

DELIMITER $$
CREATE TRIGGER `tg_schedule_details_remaining_bi`
BEFORE INSERT ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0) - COALESCE(NEW.defect_qty, 0);
END$$

CREATE TRIGGER `tg_schedule_details_remaining_bu`
BEFORE UPDATE ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0) - COALESCE(NEW.defect_qty, 0);
END$$
DELIMITER ;

-- 3) 在庫ログ → schedule_details（実績・不良）
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ai`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_au`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ad`;

DELIMITER $$

CREATE TRIGGER `tg_stl_sync_schedule_details_ai`
AFTER INSERT ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF NEW.transaction_time IS NOT NULL AND NEW.target_cd IS NOT NULL THEN
        IF NEW.transaction_type = '実績' AND NEW.machine_cd IS NOT NULL THEN
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

        IF NEW.transaction_type = '不良'
           AND TRIM(IFNULL(NEW.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    TRIM(stl.target_cd) AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS dq
                FROM stock_transaction_logs stl
                WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
                  AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
                  AND TRIM(stl.target_cd) COLLATE utf8mb4_unicode_ci = TRIM(NEW.target_cd) COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
            SET sd.defect_qty = COALESCE(agg.dq, 0)
            WHERE sd.schedule_date = DATE(NEW.transaction_time)
              AND TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci = TRIM(NEW.target_cd) COLLATE utf8mb4_unicode_ci
              AND (NEW.machine_cd IS NULL OR m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci);
        END IF;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_au`
AFTER UPDATE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF OLD.transaction_time IS NOT NULL AND OLD.target_cd IS NOT NULL THEN
        IF OLD.transaction_type = '実績' AND OLD.machine_cd IS NOT NULL THEN
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
        IF OLD.transaction_type = '不良'
           AND TRIM(IFNULL(OLD.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    TRIM(stl.target_cd) AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS dq
                FROM stock_transaction_logs stl
                WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
                  AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
                  AND TRIM(stl.target_cd) COLLATE utf8mb4_unicode_ci = TRIM(OLD.target_cd) COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
            SET sd.defect_qty = COALESCE(agg.dq, 0)
            WHERE sd.schedule_date = DATE(OLD.transaction_time)
              AND TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci = TRIM(OLD.target_cd) COLLATE utf8mb4_unicode_ci
              AND (OLD.machine_cd IS NULL OR m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci);
        END IF;
    END IF;

    IF NEW.transaction_time IS NOT NULL AND NEW.target_cd IS NOT NULL THEN
        IF NEW.transaction_type = '実績' AND NEW.machine_cd IS NOT NULL THEN
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
        IF NEW.transaction_type = '不良'
           AND TRIM(IFNULL(NEW.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    TRIM(stl.target_cd) AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS dq
                FROM stock_transaction_logs stl
                WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
                  AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
                  AND TRIM(stl.target_cd) COLLATE utf8mb4_unicode_ci = TRIM(NEW.target_cd) COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
            SET sd.defect_qty = COALESCE(agg.dq, 0)
            WHERE sd.schedule_date = DATE(NEW.transaction_time)
              AND TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci = TRIM(NEW.target_cd) COLLATE utf8mb4_unicode_ci
              AND (NEW.machine_cd IS NULL OR m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci);
        END IF;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_ad`
AFTER DELETE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF OLD.transaction_time IS NOT NULL AND OLD.target_cd IS NOT NULL THEN
        IF OLD.transaction_type = '実績' AND OLD.machine_cd IS NOT NULL THEN
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
        IF OLD.transaction_type = '不良'
           AND TRIM(IFNULL(OLD.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    TRIM(stl.target_cd) AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS dq
                FROM stock_transaction_logs stl
                WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
                  AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
                  AND TRIM(stl.target_cd) COLLATE utf8mb4_unicode_ci = TRIM(OLD.target_cd) COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
            SET sd.defect_qty = COALESCE(agg.dq, 0)
            WHERE sd.schedule_date = DATE(OLD.transaction_time)
              AND TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci = TRIM(OLD.target_cd) COLLATE utf8mb4_unicode_ci
              AND (OLD.machine_cd IS NULL OR m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci);
        END IF;
    END IF;
END$$

DELIMITER ;

-- 4) 既存明細の不良・残を一括補正（defect_qty 列追加直後）
UPDATE schedule_details sd
JOIN production_schedules ps ON ps.id = sd.schedule_id
JOIN machines m ON m.id = ps.line_id
LEFT JOIN (
    SELECT
        DATE(stl.transaction_time) AS d,
        TRIM(stl.target_cd) AS product_cd,
        COALESCE(SUM(stl.quantity), 0) AS dq
    FROM stock_transaction_logs stl
    WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
      AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
      AND stl.transaction_time IS NOT NULL
      AND stl.target_cd IS NOT NULL
    GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
) agg
  ON agg.d = sd.schedule_date
 AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
SET sd.defect_qty = COALESCE(agg.dq, 0);

UPDATE schedule_details
SET remaining_qty = COALESCE(planned_qty, 0) - COALESCE(actual_qty, 0) - COALESCE(defect_qty, 0);
