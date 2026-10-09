-- TRIGGER (schedule_details): trg_schedule_details_after_update_sync_plan_excel
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_schedule_details_after_update_sync_plan_excel`;

DELIMITER $$
CREATE TRIGGER `trg_schedule_details_after_update_sync_plan_excel` AFTER UPDATE ON `schedule_details` FOR EACH ROW BEGIN
  DECLARE v_old_machine_name VARCHAR(100);
  DECLARE v_old_product_cd VARCHAR(50);
  DECLARE v_old_order_no INT;
  DECLARE v_new_machine_name VARCHAR(100);
  DECLARE v_new_product_cd VARCHAR(50);
  DECLARE v_new_product_name VARCHAR(255);
  DECLARE v_new_order_no INT;

  SELECT m.`machine_name`, ps.`product_cd`, ps.`order_no`
    INTO v_old_machine_name, v_old_product_cd, v_old_order_no
  FROM `production_schedules` ps
  INNER JOIN `machines` m ON m.`id` = ps.`line_id`
  WHERE ps.`id` = OLD.`schedule_id`
  LIMIT 1;

  SELECT m.`machine_name`, ps.`product_cd`, ps.`item_name`, ps.`order_no`
    INTO v_new_machine_name, v_new_product_cd, v_new_product_name, v_new_order_no
  FROM `production_schedules` ps
  INNER JOIN `machines` m ON m.`id` = ps.`line_id`
  WHERE ps.`id` = NEW.`schedule_id`
  LIMIT 1;

  IF OLD.`schedule_date` IS NOT NULL
     AND v_old_machine_name IS NOT NULL
     AND v_old_product_cd IS NOT NULL THEN
    DELETE FROM `production_plan_excel`
    WHERE `日付` = OLD.`schedule_date`
      AND (`加工機` COLLATE utf8mb4_ja_0900_as_cs) = (v_old_machine_name COLLATE utf8mb4_ja_0900_as_cs)
      AND (`製品CD` COLLATE utf8mb4_ja_0900_as_cs) = (v_old_product_cd COLLATE utf8mb4_ja_0900_as_cs)
      AND (`生産順番` COLLATE utf8mb4_ja_0900_as_cs) = (CAST(LEAST(GREATEST(COALESCE(v_old_order_no, 0), 0), 99) AS CHAR) COLLATE utf8mb4_ja_0900_as_cs);
  END IF;

  IF NEW.`schedule_date` IS NOT NULL
     AND v_new_machine_name IS NOT NULL
     AND v_new_product_cd IS NOT NULL
     AND v_new_product_name IS NOT NULL
     AND NEW.`planned_qty` IS NOT NULL THEN
    INSERT INTO `production_plan_excel` (
      `日付`, `加工機`, `製品CD`, `製品名`, `加工計画`, `生産順番`
    ) VALUES (
      NEW.`schedule_date`,
      v_new_machine_name,
      v_new_product_cd,
      v_new_product_name,
      NEW.`planned_qty`,
      CAST(LEAST(GREATEST(COALESCE(v_new_order_no, 0), 0), 99) AS CHAR)
    )
    ON DUPLICATE KEY UPDATE
      `製品名` = VALUES(`製品名`),
      `加工計画` = VALUES(`加工計画`);
  END IF;
END$$
DELIMITER ;
