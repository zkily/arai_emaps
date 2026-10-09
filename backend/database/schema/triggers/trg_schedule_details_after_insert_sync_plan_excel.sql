-- TRIGGER (schedule_details): trg_schedule_details_after_insert_sync_plan_excel
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_schedule_details_after_insert_sync_plan_excel`;

DELIMITER $$
CREATE TRIGGER `trg_schedule_details_after_insert_sync_plan_excel` AFTER INSERT ON `schedule_details` FOR EACH ROW BEGIN
  DECLARE v_machine_name VARCHAR(100);
  DECLARE v_product_cd VARCHAR(50);
  DECLARE v_product_name VARCHAR(255);
  DECLARE v_order_no INT;

  SELECT m.`machine_name`, ps.`product_cd`, ps.`item_name`, ps.`order_no`
    INTO v_machine_name, v_product_cd, v_product_name, v_order_no
  FROM `production_schedules` ps
  INNER JOIN `machines` m ON m.`id` = ps.`line_id`
  WHERE ps.`id` = NEW.`schedule_id`
  LIMIT 1;

  IF NEW.`schedule_date` IS NOT NULL
     AND v_machine_name IS NOT NULL
     AND v_product_cd IS NOT NULL
     AND v_product_name IS NOT NULL
     AND NEW.`planned_qty` IS NOT NULL THEN
    INSERT INTO `production_plan_excel` (
      `日付`, `加工機`, `製品CD`, `製品名`, `加工計画`, `生産順番`
    ) VALUES (
      NEW.`schedule_date`,
      v_machine_name,
      v_product_cd,
      v_product_name,
      NEW.`planned_qty`,
      CAST(LEAST(GREATEST(COALESCE(v_order_no, 0), 0), 99) AS CHAR)
    )
    ON DUPLICATE KEY UPDATE
      `製品名` = VALUES(`製品名`),
      `加工計画` = VALUES(`加工計画`);
  END IF;
END$$
DELIMITER ;
