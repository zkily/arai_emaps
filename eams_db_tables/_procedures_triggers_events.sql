-- Procedure structure for sp_production_plan_excel_recalc_juban_for_hints
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_production_plan_excel_recalc_juban_for_hints`;
delimiter ;;
CREATE PROCEDURE `sp_production_plan_excel_recalc_juban_for_hints`()
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE v_date DATE;
  DECLARE v_machine VARCHAR(50);
  DECLARE cur CURSOR FOR
    SELECT `日付`, `加工機` FROM `production_plan_excel_juban_recalc_hint`;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  OPEN cur;
  hint_loop: LOOP
    FETCH cur INTO v_date, v_machine;
    IF done = 1 THEN
      LEAVE hint_loop;
    END IF;

    UPDATE `production_plan_excel` AS e
    INNER JOIN (
      SELECT
        id,
        ROW_NUMBER() OVER (
          PARTITION BY `日付`, `加工機`
          ORDER BY `生産順番` ASC, `id` ASC
        ) AS rn
      FROM `production_plan_excel`
      WHERE `日付` = v_date AND `加工機` = v_machine
    ) AS r ON e.id = r.id
    SET e.`順番` = CASE WHEN r.rn = 1 THEN 1 ELSE 2 END;
  END LOOP;
  CLOSE cur;

  TRUNCATE TABLE `production_plan_excel_juban_recalc_hint`;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_rebuild_and_recalc_production_plan_excel
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_rebuild_and_recalc_production_plan_excel`;
delimiter ;;
CREATE PROCEDURE `sp_rebuild_and_recalc_production_plan_excel`()
BEGIN
  CALL `sp_rebuild_production_plan_excel_all`();
  CALL `sp_recalc_junban_full`();
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_rebuild_production_plan_excel_all
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_rebuild_production_plan_excel_all`;
delimiter ;;
CREATE PROCEDURE `sp_rebuild_production_plan_excel_all`()
BEGIN
  /*
    说明：
    - 不在过程内显式 START TRANSACTION / COMMIT，避免与调用方事务冲突
    - 先清空，再从 schedule_details + production_schedules + machines 全量回填
  */
  DELETE FROM `production_plan_excel`;

  INSERT INTO `production_plan_excel` (
    `日付`,
    `加工機`,
    `製品CD`,
    `製品名`,
    `加工計画`,
    `生産順番`
  )
  SELECT
    sd.`schedule_date` AS `日付`,
    m.`machine_name`   AS `加工機`,
    ps.`product_cd`    AS `製品CD`,
    ps.`item_name`     AS `製品名`,
    sd.`planned_qty`   AS `加工計画`,
    CAST(LEAST(GREATEST(COALESCE(ps.`order_no`, 0), 0), 99) AS CHAR) AS `生産順番`
  FROM `schedule_details` sd
  INNER JOIN `production_schedules` ps
    ON ps.`id` = sd.`schedule_id`
  INNER JOIN `machines` m
    ON m.`id` = ps.`line_id`
  WHERE sd.`schedule_date` IS NOT NULL
    AND m.`machine_name` IS NOT NULL
    AND ps.`product_cd` IS NOT NULL
    AND ps.`item_name` IS NOT NULL
    AND sd.`planned_qty` IS NOT NULL
  ON DUPLICATE KEY UPDATE
    `製品名` = VALUES(`製品名`),
    `加工計画` = VALUES(`加工計画`);
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for sp_recalc_junban_full
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_recalc_junban_full`;
delimiter ;;
CREATE PROCEDURE `sp_recalc_junban_full`()
BEGIN
  UPDATE `production_plan_excel` e
  INNER JOIN (
    SELECT
      id,
      ROW_NUMBER() OVER (
        PARTITION BY `日付`, `加工機`
        ORDER BY CAST(`生産順番` AS UNSIGNED) ASC, `id` ASC
      ) AS rn
    FROM `production_plan_excel`
  ) x ON x.id = e.id
  SET e.`順番` = CASE WHEN x.rn = 1 THEN 1 ELSE 2 END;
END
;;
delimiter ;

-- ----------------------------
-- Event structure for evt_production_plan_excel_juban_recalc
-- ----------------------------
DROP EVENT IF EXISTS `evt_production_plan_excel_juban_recalc`;
delimiter ;;
CREATE EVENT `evt_production_plan_excel_juban_recalc`
ON SCHEDULE
EVERY '5' SECOND STARTS '2026-04-28 16:55:18'
ON COMPLETION PRESERVE
COMMENT '消费 juban_recalc_hint，重算各组 順番（需 event_scheduler=ON）'
DO BEGIN
  IF EXISTS (SELECT 1 FROM `production_plan_excel_juban_recalc_hint` LIMIT 1) THEN
    CALL `sp_production_plan_excel_recalc_juban_for_hints`();
  END IF;
END
;;
delimiter ;

-- ----------------------------
-- Event structure for evt_production_plan_excel_nightly_rebuild
-- ----------------------------
DROP EVENT IF EXISTS `evt_production_plan_excel_nightly_rebuild`;
delimiter ;;
CREATE EVENT `evt_production_plan_excel_nightly_rebuild`
ON SCHEDULE
EVERY '1' DAY STARTS '2026-04-29 02:30:00'
ON COMPLETION PRESERVE
COMMENT 'Nightly rebuild + junban recalc for production_plan_excel'
DO BEGIN
  CALL `sp_rebuild_and_recalc_production_plan_excel`();
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table chamfering_management
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_chamfering_management_code_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_management_code_before_insert` BEFORE INSERT ON `chamfering_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.production_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table chamfering_management
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_chamfering_management_code_before_update`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_management_code_before_update` BEFORE UPDATE ON `chamfering_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.production_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table chamfering_plans
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_chamfering_plans_code_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_plans_code_before_insert` BEFORE INSERT ON `chamfering_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.production_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
    SET NEW.cd = IF(TRIM(COALESCE(NEW.management_code, '')) != '', RIGHT(NEW.management_code, 5), NULL);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table chamfering_plans
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_chamfering_plans_code_before_update`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_plans_code_before_update` BEFORE UPDATE ON `chamfering_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.production_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
    SET NEW.cd = IF(TRIM(COALESCE(NEW.management_code, '')) != '', RIGHT(NEW.management_code, 5), NULL);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table cutting_management
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_cutting_management_code_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_cutting_management_code_before_insert` BEFORE INSERT ON `cutting_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table cutting_management
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_cutting_management_code_before_update`;
delimiter ;;
CREATE TRIGGER `tg_cutting_management_code_before_update` BEFORE UPDATE ON `cutting_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table instruction_plans
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_generate_management_code`;
delimiter ;;
CREATE TRIGGER `tg_generate_management_code` BEFORE INSERT ON `instruction_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        NEW.product_cd,
        RIGHT(NEW.production_line, 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table instruction_plans
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_update_management_code`;
delimiter ;;
CREATE TRIGGER `tg_update_management_code` BEFORE UPDATE ON `instruction_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table material_cutting_logs
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_material_cutting_logs_manufacture_no_bi`;
delimiter ;;
CREATE TRIGGER `tg_material_cutting_logs_manufacture_no_bi` BEFORE INSERT ON `material_cutting_logs` FOR EACH ROW BEGIN
    IF NEW.material_cd IS NULL OR TRIM(NEW.material_cd) = '' THEN
        SET NEW.manufacture_no = NULL;
    ELSEIF NEW.material_cd LIKE '%荒井%' THEN
        SET NEW.manufacture_no = CONCAT('A', LEFT(NEW.material_cd, 13));
    ELSEIF LEFT(LTRIM(NEW.material_cd), 1) = 'N' THEN
        SET NEW.manufacture_no = LEFT(NEW.material_cd, 8);
    ELSE
        SET NEW.manufacture_no = NEW.material_cd;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table material_cutting_logs
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_material_cutting_logs_manufacture_no_bu`;
delimiter ;;
CREATE TRIGGER `tg_material_cutting_logs_manufacture_no_bu` BEFORE UPDATE ON `material_cutting_logs` FOR EACH ROW BEGIN
    IF NEW.material_cd IS NULL OR TRIM(NEW.material_cd) = '' THEN
        SET NEW.manufacture_no = NULL;
    ELSEIF NEW.material_cd LIKE '%荒井%' THEN
        SET NEW.manufacture_no = CONCAT('A', LEFT(NEW.material_cd, 13));
    ELSEIF LEFT(LTRIM(NEW.material_cd), 1) = 'N' THEN
        SET NEW.manufacture_no = LEFT(NEW.material_cd, 8);
    ELSE
        SET NEW.manufacture_no = NEW.material_cd;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table material_stock_sub
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_material_stock_sub_current_stock_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_material_stock_sub_current_stock_before_insert` BEFORE INSERT ON `material_stock_sub` FOR EACH ROW BEGIN
  IF (COALESCE(NEW.order_quantity, 0) - COALESCE(NEW.planned_usage, 0)) > 0 THEN
    SET NEW.current_stock = 1;
  ELSE
    SET NEW.current_stock = 0;
  END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table material_stock_sub
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_material_stock_sub_current_stock_before_update`;
delimiter ;;
CREATE TRIGGER `tg_material_stock_sub_current_stock_before_update` BEFORE UPDATE ON `material_stock_sub` FOR EACH ROW BEGIN
  IF (COALESCE(NEW.order_quantity, 0) - COALESCE(NEW.planned_usage, 0)) > 0 THEN
    SET NEW.current_stock = 1;
  ELSE
    SET NEW.current_stock = 0;
  END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table order_monthly
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_order_monthly_before_insert`;
delimiter ;;
CREATE TRIGGER `trg_order_monthly_before_insert` BEFORE INSERT ON `order_monthly` FOR EACH ROW BEGIN
  DECLARE typeSuffix CHAR(1);

  SET typeSuffix = CASE NEW.product_type
    WHEN '試作品' THEN '1'
    WHEN '別注品' THEN '2'
    WHEN '補給品' THEN '3'
    WHEN 'サンプル品' THEN '4'
		WHEN '代替品' THEN '5'
		WHEN '返却品' THEN '6'
    WHEN 'その他' THEN '7'
    ELSE '0' -- 量産品
  END;

  SET NEW.order_id = CONCAT(
    NEW.year,
    LPAD(NEW.month, 2, '0'),
    NEW.destination_cd,
    NEW.product_cd,
    typeSuffix
  );
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_material_issues
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_material_issue_after_update`;
delimiter ;;
CREATE TRIGGER `trg_material_issue_after_update` AFTER UPDATE ON `outsourcing_material_issues` FOR EACH ROW BEGIN
    IF NEW.status = 'issued' AND OLD.status = 'preparing' THEN
        -- 支給材料在庫を更新
        INSERT INTO outsourcing_supplied_material_stock 
        (supplier_cd, material_cd, material_name, spec, unit, unit_weight, issued_qty, last_issue_date)
        VALUES (NEW.supplier_cd, NEW.material_cd, NEW.material_name, NEW.spec, NEW.unit, NEW.unit_weight, NEW.quantity, NEW.issue_date)
        ON DUPLICATE KEY UPDATE 
            issued_qty = issued_qty + NEW.quantity,
            last_issue_date = NEW.issue_date;
        
        -- 支給履歴を記録
        INSERT INTO outsourcing_material_transactions 
        (transaction_date, transaction_type, supplier_cd, material_cd, material_name, related_no, quantity, operator)
        VALUES (NEW.issue_date, 'issue', NEW.supplier_cd, NEW.material_cd, NEW.material_name, NEW.issue_no, NEW.quantity, NEW.operator);
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_material_usages
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_material_usage_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_material_usage_after_insert` AFTER INSERT ON `outsourcing_material_usages` FOR EACH ROW BEGIN
    -- 支給材料在庫の使用数を更新
    UPDATE outsourcing_supplied_material_stock 
    SET used_qty = used_qty + NEW.usage_qty,
        last_usage_date = NEW.usage_date
    WHERE supplier_cd = NEW.supplier_cd AND material_cd = NEW.material_cd;
    
    -- 使用履歴を記録
    INSERT INTO outsourcing_material_transactions 
    (transaction_date, transaction_type, supplier_cd, material_cd, material_name, related_no, quantity, operator)
    VALUES (NEW.usage_date, 'usage', NEW.supplier_cd, NEW.material_cd, NEW.material_name, NEW.usage_no, NEW.usage_qty, NEW.reporter);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_plating_orders
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_plating_order_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_plating_order_after_insert` AFTER INSERT ON `outsourcing_plating_orders` FOR EACH ROW BEGIN
    IF NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT06',
            '実績',
            NEW.quantity,
            COALESCE(NEW.unit, '本'),
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注メッキ注文: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_plating_orders'
        );
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_plating_orders
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_plating_order_after_update`;
delimiter ;;
CREATE TRIGGER `trg_plating_order_after_update` AFTER UPDATE ON `outsourcing_plating_orders` FOR EACH ROW BEGIN
    IF (OLD.status <> 'ordered' OR OLD.status IS NULL) AND NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT06',
            '実績',
            NEW.quantity,
            COALESCE(NEW.unit, '本'),
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注メッキ注文（発注済）: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_plating_orders'
        );
    ELSEIF NEW.status = 'ordered' AND (
        (OLD.quantity <> NEW.quantity) OR
        (OLD.unit_price <> NEW.unit_price) OR
        (OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL)) OR
        (OLD.product_cd <> NEW.product_cd)
    ) THEN
        -- 直接用更新数量方式（加减しない）：既存行を quantity=NEW.quantity で更新、なければ INSERT
        -- 照合順序の混在エラー回避: notes と NEW.order_no を utf8mb4_unicode_ci で比較
        UPDATE stock_transaction_logs SET
            target_cd = NEW.product_cd,
            location_cd = '外注倉庫',
            process_cd = 'KT06',
            quantity = NEW.quantity,
            unit = COALESCE(NEW.unit, '個'),
            transaction_time = NEW.order_date,
            notes = CONVERT(NEW.order_no USING utf8mb4) COLLATE utf8mb4_unicode_ci,
            remarks = CONCAT('外注メッキ注文（発注済）: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
            source_file = 'outsourcing_plating_orders'
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.order_no COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_orders'
          AND process_cd = 'KT06'
          AND transaction_type = '実績';

        IF ROW_COUNT() = 0 THEN
            INSERT INTO stock_transaction_logs (
                stock_type,
                target_cd,
                location_cd,
                process_cd,
                transaction_type,
                quantity,
                unit,
                transaction_time,
                notes,
                remarks,
                source_file
            ) VALUES (
                '仕掛品',
                NEW.product_cd,
                '外注倉庫',
                'KT06',
                '実績',
                NEW.quantity,
                COALESCE(NEW.unit, '個'),
                NEW.order_date,
                NEW.order_no,
                CONCAT('外注メッキ注文（発注済）: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
                'outsourcing_plating_orders'
            );
        END IF;
    ELSEIF OLD.status = 'ordered' AND NEW.status = 'cancelled' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            OLD.product_cd,
            '外注倉庫',
            'KT06',
            '実績',
            -OLD.quantity,
            COALESCE(OLD.unit, '個'),
            OLD.order_date,
            OLD.order_no,
            CONCAT('外注メッキ注文取消: ', COALESCE(OLD.product_name, ''), ' | 注文番号: ', OLD.order_no,
                   ' | 状態: ', OLD.status, '→', NEW.status, ' | 外注先: ', OLD.supplier_cd),
            'outsourcing_plating_orders'
        );
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_plating_receivings
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_plating_receiving_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_plating_receiving_after_insert` AFTER INSERT ON `outsourcing_plating_receivings` FOR EACH ROW BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_plating_receivings WHERE order_id = NEW.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_plating_orders WHERE id = NEW.order_id LIMIT 1;

    UPDATE outsourcing_plating_orders
    SET received_qty = received_qty + COALESCE(NEW.good_qty, 0),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty + COALESCE(NEW.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = NEW.order_id;

    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        UPDATE outsourcing_plating_stock
        SET received_qty = received_qty + NEW.good_qty,
            last_receive_date = NEW.receiving_date
        WHERE product_cd = NEW.product_cd
          AND supplier_cd = NEW.supplier_cd
        LIMIT 1;

        IF ROW_COUNT() = 0 THEN
            INSERT INTO outsourcing_plating_stock
                (product_cd, product_name, supplier_cd, plating_type, received_qty, last_receive_date)
            VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.plating_type, NEW.good_qty, NEW.receiving_date);
        END IF;
    END IF;

    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date, 'receive', 'plating',
            NEW.product_cd, NEW.product_name, NEW.supplier_cd,
            NEW.receiving_no, NEW.good_qty, NEW.inspector
        );
    END IF;

    -- 良品数が 0 のときは実績行を保存しない
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT17' COLLATE utf8mb4_unicode_ci,
            '実績' COLLATE utf8mb4_unicode_ci,
            NEW.good_qty,
            '本' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            CONCAT(
                '外注メッキ受入: ', COALESCE(NEW.product_name, ''),
                ' | 受入番号: ', NEW.receiving_no,
                ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
                ' | 良品: ', NEW.good_qty,
                ' | 不良: ', COALESCE(NEW.defect_qty, 0),
                ' | 外注先: ', NEW.supplier_cd,
                IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
            ) COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_plating_receivings'
        );
    END IF;
    -- 不良数が 0 のときは不良行を保存しない
    IF COALESCE(NEW.defect_qty, 0) > 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT17' COLLATE utf8mb4_unicode_ci,
            '不良' COLLATE utf8mb4_unicode_ci,
            NEW.defect_qty,
            '本' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            CONCAT(
                '外注メッキ受入: ', COALESCE(NEW.product_name, ''),
                ' | 受入番号: ', NEW.receiving_no,
                ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
                ' | 良品: ', COALESCE(NEW.good_qty, 0),
                ' | 不良: ', NEW.defect_qty,
                ' | 外注先: ', NEW.supplier_cd,
                IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
            ) COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_plating_receivings'
        );
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_plating_receivings
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_plating_receiving_after_update`;
delimiter ;;
CREATE TRIGGER `trg_plating_receiving_after_update` AFTER UPDATE ON `outsourcing_plating_receivings` FOR EACH ROW BEGIN
    DECLARE total_good INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;
    DECLARE stock_received INT DEFAULT 0;

    -- 該当注文の受入良品合計で直接セット
    SELECT COALESCE(SUM(good_qty), 0) INTO total_good
    FROM outsourcing_plating_receivings WHERE order_id = NEW.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_plating_orders WHERE id = NEW.order_id LIMIT 1;

    UPDATE outsourcing_plating_orders
    SET received_qty = total_good,
        status = CASE
            WHEN total_good >= order_qty_val THEN 'completed'
            WHEN total_good > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = NEW.order_id;

    -- 該当 product_cd + supplier_cd の受入良品合計で直接セット
    SELECT COALESCE(SUM(good_qty), 0) INTO stock_received
    FROM outsourcing_plating_receivings
    WHERE product_cd = NEW.product_cd AND supplier_cd = NEW.supplier_cd;

    UPDATE outsourcing_plating_stock
    SET received_qty = stock_received,
        last_receive_date = NEW.receiving_date
    WHERE product_cd = NEW.product_cd
      AND supplier_cd = NEW.supplier_cd
    LIMIT 1;

    IF ROW_COUNT() = 0 AND stock_received > 0 THEN
        INSERT INTO outsourcing_plating_stock
            (product_cd, product_name, supplier_cd, plating_type, received_qty, last_receive_date)
        VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.plating_type, stock_received, NEW.receiving_date);
    END IF;

    INSERT INTO outsourcing_stock_transactions
        (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
    VALUES (
        NEW.receiving_date, 'receive', 'plating',
        NEW.product_cd, NEW.product_name, NEW.supplier_cd,
        NEW.receiving_no, COALESCE(NEW.good_qty, 0) - COALESCE(OLD.good_qty, 0), NEW.inspector
    );
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_plating_receivings
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_plating_receiving_to_stock_logs_update`;
delimiter ;;
CREATE TRIGGER `trg_plating_receiving_to_stock_logs_update` AFTER UPDATE ON `outsourcing_plating_receivings` FOR EACH ROW BEGIN
    DECLARE _remarks TEXT;

    SET _remarks = CONCAT(
        '外注メッキ受入: ', COALESCE(NEW.product_name, ''),
        ' | 受入番号: ', NEW.receiving_no,
        ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
        ' | 良品: ', COALESCE(NEW.good_qty, 0),
        ' | 不良: ', COALESCE(NEW.defect_qty, 0),
        ' | 外注先: ', NEW.supplier_cd,
        IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
    );

    -- 良品行（実績）：良品数>0 のときのみ更新または挿入、0 のときは削除
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        UPDATE stock_transaction_logs SET
            target_cd = NEW.product_cd,
            location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            process_cd = 'KT17' COLLATE utf8mb4_unicode_ci,
            transaction_type = '実績' COLLATE utf8mb4_unicode_ci,
            quantity = NEW.good_qty,
            unit = '本' COLLATE utf8mb4_unicode_ci,
            transaction_time = CAST(NEW.receiving_date AS DATETIME),
            remarks = _remarks COLLATE utf8mb4_unicode_ci,
            unit_price = 0,
            source_file = 'outsourcing_plating_receivings'
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '実績' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';

        IF ROW_COUNT() = 0 THEN
            INSERT INTO stock_transaction_logs (
                stock_type, target_cd, location_cd, process_cd, transaction_type,
                quantity, unit, transaction_time, notes, remarks, unit_price, source_file
            ) VALUES (
                '仕掛品' COLLATE utf8mb4_unicode_ci,
                NEW.product_cd,
                '仕上倉庫' COLLATE utf8mb4_unicode_ci,
                'KT17' COLLATE utf8mb4_unicode_ci,
                '実績' COLLATE utf8mb4_unicode_ci,
                NEW.good_qty,
                '本' COLLATE utf8mb4_unicode_ci,
                CAST(NEW.receiving_date AS DATETIME),
                NEW.receiving_no,
                _remarks COLLATE utf8mb4_unicode_ci,
                0,
                'outsourcing_plating_receivings'
            );
        END IF;
    ELSE
        DELETE FROM stock_transaction_logs
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '実績' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';
    END IF;

    -- 不良行（不良）：不良数>0 のときのみ更新または挿入、0 のときは削除
    IF COALESCE(NEW.defect_qty, 0) > 0 THEN
        UPDATE stock_transaction_logs SET
            target_cd = NEW.product_cd,
            location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            process_cd = 'KT17' COLLATE utf8mb4_unicode_ci,
            transaction_type = '不良' COLLATE utf8mb4_unicode_ci,
            quantity = NEW.defect_qty,
            unit = '本' COLLATE utf8mb4_unicode_ci,
            transaction_time = CAST(NEW.receiving_date AS DATETIME),
            remarks = _remarks COLLATE utf8mb4_unicode_ci,
            unit_price = 0,
            source_file = 'outsourcing_plating_receivings'
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '不良' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';

        IF ROW_COUNT() = 0 THEN
            INSERT INTO stock_transaction_logs (
                stock_type, target_cd, location_cd, process_cd, transaction_type,
                quantity, unit, transaction_time, notes, remarks, unit_price, source_file
            ) VALUES (
                '仕掛品' COLLATE utf8mb4_unicode_ci,
                NEW.product_cd,
                '仕上倉庫' COLLATE utf8mb4_unicode_ci,
                'KT17' COLLATE utf8mb4_unicode_ci,
                '不良' COLLATE utf8mb4_unicode_ci,
                NEW.defect_qty,
                '本' COLLATE utf8mb4_unicode_ci,
                CAST(NEW.receiving_date AS DATETIME),
                NEW.receiving_no,
                _remarks COLLATE utf8mb4_unicode_ci,
                0,
                'outsourcing_plating_receivings'
            );
        END IF;
    ELSE
        DELETE FROM stock_transaction_logs
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '不良' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_plating_receivings
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_plating_receiving_after_delete`;
delimiter ;;
CREATE TRIGGER `trg_plating_receiving_after_delete` AFTER DELETE ON `outsourcing_plating_receivings` FOR EACH ROW BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_plating_receivings WHERE order_id = OLD.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_plating_orders WHERE id = OLD.order_id LIMIT 1;

    UPDATE outsourcing_plating_orders
    SET received_qty = GREATEST(0, received_qty - COALESCE(OLD.good_qty, 0)),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty - COALESCE(OLD.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = OLD.order_id;

    IF COALESCE(OLD.good_qty, 0) > 0 THEN
        UPDATE outsourcing_plating_stock
        SET received_qty = GREATEST(0, received_qty - OLD.good_qty)
        WHERE product_cd = OLD.product_cd
          AND supplier_cd = OLD.supplier_cd
        ORDER BY id
        LIMIT 1;

        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            OLD.receiving_date, 'receive', 'plating',
            OLD.product_cd, OLD.product_name, OLD.supplier_cd,
            OLD.receiving_no, -OLD.good_qty, OLD.inspector
        );
    END IF;

    DELETE FROM stock_transaction_logs
    WHERE notes = OLD.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
      AND source_file = 'outsourcing_plating_receivings';
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_welding_orders
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_order_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_welding_order_after_insert` AFTER INSERT ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
    -- 只有当 status = 'ordered'（発注済）时才记录
IF NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文: ', NEW.product_name, ' | 外注先: ', NEW.supplier_cd),
            NEW.unit_price,
            'outsourcing_welding_orders'
        );
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_welding_orders
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_order_after_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_order_after_update` AFTER UPDATE ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
    -- 情况1：status 从其他值变为 'ordered'（発注済）时，记录新订单
    IF (OLD.status <> 'ordered' OR OLD.status IS NULL) AND NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文（発注済）: ', NEW.product_name, ' | 外注先: ', NEW.supplier_cd),
            NEW.unit_price,
            'outsourcing_welding_orders'
        );
    ELSEIF NEW.status = 'ordered' AND (
        (OLD.quantity <> NEW.quantity) OR
        (OLD.unit_price <> NEW.unit_price) OR
        (OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL)) OR
        (OLD.product_cd <> NEW.product_cd)
    ) THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity - OLD.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文変更（発注済）: ', NEW.product_name,
                   IF(OLD.quantity <> NEW.quantity, CONCAT(' | 数量: ', OLD.quantity, '→', NEW.quantity), ''),
                   IF(OLD.unit_price <> NEW.unit_price, CONCAT(' | 単価: ', OLD.unit_price, '→', NEW.unit_price), ''),
                   IF(OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL), CONCAT(' | 納期変更'), ''),
                   ' | 外注先: ', NEW.supplier_cd
            ),
            NEW.unit_price,
            'outsourcing_welding_orders'
        );
    ELSEIF OLD.status = 'ordered' AND NEW.status = 'cancelled' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品',
            OLD.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            -OLD.quantity,
            OLD.unit,
            OLD.order_date,
            OLD.order_no,
            CONCAT('外注溶接注文取消: ', OLD.product_name, ' | 注文番号: ', OLD.order_no,
                   ' | 状態: ', OLD.status, '→', NEW.status, ' | 外注先: ', OLD.supplier_cd),
            OLD.unit_price,
            'outsourcing_welding_orders'
        );
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_welding_orders
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_order_update_sync_receivings`;
delimiter ;;
CREATE TRIGGER `trg_welding_order_update_sync_receivings` AFTER UPDATE ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
    -- 如果关键字段发生变化，更新相关的受入记录
    IF (OLD.product_cd <> NEW.product_cd OR 
        OLD.product_name <> NEW.product_name OR 
        (OLD.product_name IS NULL AND NEW.product_name IS NOT NULL) OR
        (OLD.product_name IS NOT NULL AND NEW.product_name IS NULL) OR
        OLD.supplier_cd <> NEW.supplier_cd OR
        OLD.welding_type <> NEW.welding_type OR
        (OLD.welding_type IS NULL AND NEW.welding_type IS NOT NULL) OR
        (OLD.welding_type IS NOT NULL AND NEW.welding_type IS NULL) OR
        OLD.delivery_location <> NEW.delivery_location OR
        (OLD.delivery_location IS NULL AND NEW.delivery_location IS NOT NULL) OR
        (OLD.delivery_location IS NOT NULL AND NEW.delivery_location IS NULL) OR
        OLD.category <> NEW.category OR
        (OLD.category IS NULL AND NEW.category IS NOT NULL) OR
        (OLD.category IS NOT NULL AND NEW.category IS NULL) OR
        OLD.content <> NEW.content OR
        (OLD.content IS NULL AND NEW.content IS NOT NULL) OR
        (OLD.content IS NOT NULL AND NEW.content IS NULL) OR
        OLD.specification <> NEW.specification OR
        (OLD.specification IS NULL AND NEW.specification IS NOT NULL) OR
        (OLD.specification IS NOT NULL AND NEW.specification IS NULL)) THEN
        
        -- 更新所有相关的受入记录
        UPDATE outsourcing_welding_receivings
        SET 
            product_cd = NEW.product_cd,
            product_name = NEW.product_name,
            supplier_cd = NEW.supplier_cd,
            welding_type = NEW.welding_type,
            delivery_location = NEW.delivery_location,
            category = NEW.category,
            content = NEW.content,
            specification = NEW.specification
        WHERE order_id = NEW.id;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_welding_orders
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_order_update_sync_stock`;
delimiter ;;
CREATE TRIGGER `trg_welding_order_update_sync_stock` AFTER UPDATE ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
    -- 如果产品代码、外注先代码或溶接种类发生变化，需要处理在庫迁移
    IF (OLD.product_cd <> NEW.product_cd OR 
        OLD.supplier_cd <> NEW.supplier_cd OR
        OLD.welding_type <> NEW.welding_type OR
        (OLD.welding_type IS NULL AND NEW.welding_type IS NOT NULL) OR
        (OLD.welding_type IS NOT NULL AND NEW.welding_type IS NULL)) THEN
        
        -- 情况1：如果产品名称也发生变化，更新在庫记录的产品名称
        IF (OLD.product_name <> NEW.product_name OR
            (OLD.product_name IS NULL AND NEW.product_name IS NOT NULL) OR
            (OLD.product_name IS NOT NULL AND NEW.product_name IS NULL)) THEN
            
            -- 更新新键值的在庫记录的产品名称
            UPDATE outsourcing_welding_stock
            SET product_name = NEW.product_name
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type = NEW.welding_type OR (welding_type IS NULL AND NEW.welding_type IS NULL));
        END IF;
        
        -- 注意：在庫数量不应该因为订单更新而改变
        -- 在庫数量是通过受入记录（good_qty）累加的
        -- 如果订单的产品代码或外注先变化，在庫记录应该保持不变
        -- 因为实际的在庫是基于 product_cd + supplier_cd + welding_type 的组合
        
    -- 如果只是产品名称变化，更新在庫记录
    ELSEIF (OLD.product_name <> NEW.product_name OR
            (OLD.product_name IS NULL AND NEW.product_name IS NOT NULL) OR
            (OLD.product_name IS NOT NULL AND NEW.product_name IS NULL)) THEN
        
        -- 更新在庫记录的产品名称
        UPDATE outsourcing_welding_stock
        SET product_name = NEW.product_name
        WHERE product_cd = NEW.product_cd
          AND supplier_cd = NEW.supplier_cd
          AND (welding_type = NEW.welding_type OR (welding_type IS NULL AND NEW.welding_type IS NULL));
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_welding_receivings
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_receiving_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_insert` AFTER INSERT ON `outsourcing_welding_receivings` FOR EACH ROW BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    -- 注文：入庫数に良品数を加算、状態は受入数合计>=注文数で completed
    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_welding_receivings WHERE order_id = NEW.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = NEW.order_id LIMIT 1;

    UPDATE outsourcing_welding_orders
    SET received_qty = received_qty + COALESCE(NEW.good_qty, 0),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty + COALESCE(NEW.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = NEW.order_id;

    -- 溶接品在庫：良品>0 のときのみ。先 UPDATE、該当行がなければ INSERT（NULL welding_type 対応）
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        UPDATE outsourcing_welding_stock
        SET received_qty = received_qty + NEW.good_qty,
            last_receive_date = NEW.receiving_date
        WHERE product_cd = NEW.product_cd
          AND supplier_cd = NEW.supplier_cd
          AND (welding_type <=> NEW.welding_type)
        LIMIT 1;

        IF ROW_COUNT() = 0 THEN
            INSERT INTO outsourcing_welding_stock
                (product_cd, product_name, supplier_cd, welding_type, received_qty, last_receive_date)
            VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.welding_type, NEW.good_qty, NEW.receiving_date);
        END IF;
    END IF;

    -- 入出庫履歴：良品>0 のときのみ
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date, 'receive', 'welding',
            NEW.product_cd, NEW.product_name, NEW.supplier_cd,
            NEW.receiving_no, NEW.good_qty, NEW.inspector
        );
    END IF;

    -- stock_transaction_logs：良品行（実績）・不良行（不良）を登録
    INSERT INTO stock_transaction_logs (
        stock_type, target_cd, location_cd, process_cd, transaction_type,
        quantity, unit, transaction_time, notes, remarks, unit_price, source_file
    ) VALUES (
        '仕掛品' COLLATE utf8mb4_unicode_ci,
        NEW.product_cd,
        '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        'KT16' COLLATE utf8mb4_unicode_ci,
        '実績' COLLATE utf8mb4_unicode_ci,
        COALESCE(NEW.good_qty, 0),
        '本' COLLATE utf8mb4_unicode_ci,
        CAST(NEW.receiving_date AS DATETIME),
        NEW.receiving_no,
        CONCAT(
            '外注溶接受入: ', COALESCE(NEW.product_name, ''),
            ' | 受入番号: ', NEW.receiving_no,
            ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
            ' | 良品: ', COALESCE(NEW.good_qty, 0),
            ' | 不良: ', COALESCE(NEW.defect_qty, 0),
            ' | 外注先: ', NEW.supplier_cd,
            IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
        ) COLLATE utf8mb4_unicode_ci,
        0,
        'outsourcing_welding_receivings'
    );
    INSERT INTO stock_transaction_logs (
        stock_type, target_cd, location_cd, process_cd, transaction_type,
        quantity, unit, transaction_time, notes, remarks, unit_price, source_file
    ) VALUES (
        '仕掛品' COLLATE utf8mb4_unicode_ci,
        NEW.product_cd,
        '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        'KT16' COLLATE utf8mb4_unicode_ci,
        '不良' COLLATE utf8mb4_unicode_ci,
        COALESCE(NEW.defect_qty, 0),
        '本' COLLATE utf8mb4_unicode_ci,
        CAST(NEW.receiving_date AS DATETIME),
        NEW.receiving_no,
        CONCAT(
            '外注溶接受入: ', COALESCE(NEW.product_name, ''),
            ' | 受入番号: ', NEW.receiving_no,
            ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
            ' | 良品: ', COALESCE(NEW.good_qty, 0),
            ' | 不良: ', COALESCE(NEW.defect_qty, 0),
            ' | 外注先: ', NEW.supplier_cd,
            IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
        ) COLLATE utf8mb4_unicode_ci,
        0,
        'outsourcing_welding_receivings'
    );
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_welding_receivings
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_receiving_after_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_update` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW BEGIN
    DECLARE good_qty_diff INT DEFAULT 0;
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    SET good_qty_diff = COALESCE(NEW.good_qty, 0) - COALESCE(OLD.good_qty, 0);

    IF good_qty_diff != 0 THEN
        SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
        FROM outsourcing_welding_receivings WHERE order_id = NEW.order_id;
        SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = NEW.order_id LIMIT 1;

        UPDATE outsourcing_welding_orders
        SET received_qty = GREATEST(0, received_qty + good_qty_diff),
            status = CASE
                WHEN total_received >= order_qty_val THEN 'completed'
                WHEN received_qty + good_qty_diff > 0 THEN 'partial'
                ELSE 'ordered'
            END
        WHERE id = NEW.order_id;

        IF good_qty_diff > 0 THEN
            UPDATE outsourcing_welding_stock
            SET received_qty = received_qty + good_qty_diff,
                last_receive_date = NEW.receiving_date
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type <=> NEW.welding_type)
            LIMIT 1;
            IF ROW_COUNT() = 0 THEN
                INSERT INTO outsourcing_welding_stock
                    (product_cd, product_name, supplier_cd, welding_type, received_qty, last_receive_date)
                VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.welding_type, good_qty_diff, NEW.receiving_date);
            END IF;
        ELSE
            UPDATE outsourcing_welding_stock
            SET received_qty = GREATEST(0, received_qty + good_qty_diff)
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type <=> NEW.welding_type)
            ORDER BY id
            LIMIT 1;
        END IF;

        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date, 'receive', 'welding',
            NEW.product_cd, NEW.product_name, NEW.supplier_cd,
            NEW.receiving_no, good_qty_diff, NEW.inspector
        );
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_welding_receivings
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_receiving_to_stock_logs_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_to_stock_logs_update` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW BEGIN
    DECLARE _remarks TEXT;

    SET _remarks = CONCAT(
        '外注溶接受入: ', COALESCE(NEW.product_name, ''),
        ' | 受入番号: ', NEW.receiving_no,
        ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
        ' | 良品: ', COALESCE(NEW.good_qty, 0),
        ' | 不良: ', COALESCE(NEW.defect_qty, 0),
        ' | 外注先: ', NEW.supplier_cd,
        IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
    );

    -- 良品行（操作種別=実績、quantity=良品数）
    UPDATE stock_transaction_logs SET
        target_cd = NEW.product_cd,
        location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        process_cd = 'KT16' COLLATE utf8mb4_unicode_ci,
        transaction_type = '実績' COLLATE utf8mb4_unicode_ci,
        quantity = COALESCE(NEW.good_qty, 0),
        unit = '本' COLLATE utf8mb4_unicode_ci,
        transaction_time = CAST(NEW.receiving_date AS DATETIME),
        remarks = _remarks COLLATE utf8mb4_unicode_ci,
        unit_price = 0,
        source_file = 'outsourcing_welding_receivings'
    WHERE notes = NEW.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci
      AND transaction_type = '実績' COLLATE utf8mb4_unicode_ci;

    IF ROW_COUNT() = 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT16' COLLATE utf8mb4_unicode_ci,
            '実績' COLLATE utf8mb4_unicode_ci,
            COALESCE(NEW.good_qty, 0),
            '本' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            _remarks COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_welding_receivings'
        );
    END IF;

    -- 不良行（操作種別=不良、quantity=不良数）
    UPDATE stock_transaction_logs SET
        target_cd = NEW.product_cd,
        location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        process_cd = 'KT16' COLLATE utf8mb4_unicode_ci,
        transaction_type = '不良' COLLATE utf8mb4_unicode_ci,
        quantity = COALESCE(NEW.defect_qty, 0),
        unit = '本' COLLATE utf8mb4_unicode_ci,
        transaction_time = CAST(NEW.receiving_date AS DATETIME),
        remarks = _remarks COLLATE utf8mb4_unicode_ci,
        unit_price = 0,
        source_file = 'outsourcing_welding_receivings'
    WHERE notes = NEW.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci
      AND transaction_type = '不良' COLLATE utf8mb4_unicode_ci;

    IF ROW_COUNT() = 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT16' COLLATE utf8mb4_unicode_ci,
            '不良' COLLATE utf8mb4_unicode_ci,
            COALESCE(NEW.defect_qty, 0),
            '本' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            _remarks COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_welding_receivings'
        );
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table outsourcing_welding_receivings
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_receiving_after_delete`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_delete` AFTER DELETE ON `outsourcing_welding_receivings` FOR EACH ROW BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    -- 削除後残りの受入数合计（当該行は既に削除済み）
    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_welding_receivings WHERE order_id = OLD.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = OLD.order_id LIMIT 1;

    UPDATE outsourcing_welding_orders
    SET received_qty = GREATEST(0, received_qty - COALESCE(OLD.good_qty, 0)),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty - COALESCE(OLD.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = OLD.order_id;

    IF COALESCE(OLD.good_qty, 0) > 0 THEN
        UPDATE outsourcing_welding_stock
        SET received_qty = GREATEST(0, received_qty - OLD.good_qty)
        WHERE product_cd = OLD.product_cd
          AND supplier_cd = OLD.supplier_cd
          AND (welding_type <=> OLD.welding_type)
        ORDER BY id
        LIMIT 1;

        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            OLD.receiving_date, 'receive', 'welding',
            OLD.product_cd, OLD.product_name, OLD.supplier_cd,
            OLD.receiving_no, -OLD.good_qty, OLD.inspector
        );
    END IF;

    -- stock_transaction_logs：当該受入の良品行・不良行を削除
    DELETE FROM stock_transaction_logs
    WHERE notes = OLD.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci
      AND source_file = 'outsourcing_welding_receivings';
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table schedule_details
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bi`;
delimiter ;;
CREATE TRIGGER `tg_schedule_details_remaining_bi` BEFORE INSERT ON `schedule_details` FOR EACH ROW BEGIN
    SET NEW.remaining_qty = COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0) - COALESCE(NEW.defect_qty, 0);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table schedule_details
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bu`;
delimiter ;;
CREATE TRIGGER `tg_schedule_details_remaining_bu` BEFORE UPDATE ON `schedule_details` FOR EACH ROW BEGIN
    SET NEW.remaining_qty = COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0) - COALESCE(NEW.defect_qty, 0);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table shipping_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_shipping_items_before_insert`;
delimiter ;;
CREATE TRIGGER `trg_shipping_items_before_insert` BEFORE INSERT ON `shipping_items` FOR EACH ROW BEGIN
  SET NEW.shipping_no_p = CONCAT(NEW.shipping_no, '_', NEW.product_cd);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table shipping_items
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_shipping_items_before_update`;
delimiter ;;
CREATE TRIGGER `trg_shipping_items_before_update` BEFORE UPDATE ON `shipping_items` FOR EACH ROW BEGIN
  SET NEW.shipping_no_p = CONCAT(NEW.shipping_no, '_', NEW.product_cd);
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table stock_transaction_logs
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ai`;
delimiter ;;
CREATE TRIGGER `tg_stl_sync_schedule_details_ai` AFTER INSERT ON `stock_transaction_logs` FOR EACH ROW BEGIN
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
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table stock_transaction_logs
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_au`;
delimiter ;;
CREATE TRIGGER `tg_stl_sync_schedule_details_au` AFTER UPDATE ON `stock_transaction_logs` FOR EACH ROW BEGIN
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
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table stock_transaction_logs
-- ----------------------------
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ad`;
delimiter ;;
CREATE TRIGGER `tg_stl_sync_schedule_details_ad` AFTER DELETE ON `stock_transaction_logs` FOR EACH ROW BEGIN
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
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
