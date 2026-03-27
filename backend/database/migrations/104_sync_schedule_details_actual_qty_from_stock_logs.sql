-- schedule_details.actual_qty を stock_transaction_logs から同期
-- 条件: 同一日付 + 同一設備(machine_cd) + 同一製品(product_cd)
-- 対象トランザクション: transaction_type='実績'

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
    -- OLD キー側を再集計（移動・種別変更時の戻し）
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

    -- NEW キー側を再集計（追加/変更後）
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

-- 既存データの一括同期
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
      AND stl.machine_cd IS NOT NULL
      AND stl.target_cd IS NOT NULL
    GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
) agg
  ON agg.d = sd.schedule_date
 AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
 AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
SET sd.actual_qty = COALESCE(agg.qty, 0);
