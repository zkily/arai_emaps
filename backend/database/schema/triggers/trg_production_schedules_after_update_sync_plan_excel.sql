-- TRIGGER (production_schedules): trg_production_schedules_after_update_sync_plan_excel
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_production_schedules_after_update_sync_plan_excel`;

DELIMITER $$
CREATE TRIGGER `trg_production_schedules_after_update_sync_plan_excel` AFTER UPDATE ON `production_schedules` FOR EACH ROW BEGIN
  DECLARE v_old_machine_name VARCHAR(100);
  DECLARE v_new_machine_name VARCHAR(100);

  SELECT `machine_name`
    INTO v_old_machine_name
  FROM `machines`
  WHERE `id` = OLD.`line_id`
  LIMIT 1;

  SELECT `machine_name`
    INTO v_new_machine_name
  FROM `machines`
  WHERE `id` = NEW.`line_id`
  LIMIT 1;

  IF v_old_machine_name IS NOT NULL AND OLD.`product_cd` IS NOT NULL THEN
    DELETE ppe
    FROM `production_plan_excel` ppe
    INNER JOIN `schedule_details` sd
      ON sd.`schedule_id` = OLD.`id` AND sd.`schedule_date` = ppe.`日付`
    WHERE (ppe.`加工機` COLLATE utf8mb4_ja_0900_as_cs) = (v_old_machine_name COLLATE utf8mb4_ja_0900_as_cs)
      AND (ppe.`製品CD` COLLATE utf8mb4_ja_0900_as_cs) = (OLD.`product_cd` COLLATE utf8mb4_ja_0900_as_cs)
      AND (ppe.`生産順番` COLLATE utf8mb4_ja_0900_as_cs) = (CAST(LEAST(GREATEST(COALESCE(OLD.`order_no`, 0), 0), 99) AS CHAR) COLLATE utf8mb4_ja_0900_as_cs);
  END IF;

  IF v_new_machine_name IS NOT NULL
     AND NEW.`product_cd` IS NOT NULL
     AND NEW.`item_name` IS NOT NULL THEN
    INSERT INTO `production_plan_excel` (`日付`, `加工機`, `製品CD`, `製品名`, `加工計画`, `生産順番`)
    SELECT
      sd.`schedule_date`,
      v_new_machine_name,
      NEW.`product_cd`,
      NEW.`item_name`,
      sd.`planned_qty`,
      CAST(LEAST(GREATEST(COALESCE(NEW.`order_no`, 0), 0), 99) AS CHAR)
    FROM `schedule_details` sd
    WHERE sd.`schedule_id` = NEW.`id`
    ON DUPLICATE KEY UPDATE
      `製品名` = VALUES(`製品名`),
      `加工計画` = VALUES(`加工計画`);
  END IF;
END$$
DELIMITER ;
