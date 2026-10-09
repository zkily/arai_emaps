-- TRIGGER (schedule_details): trg_schedule_details_after_delete_sync_plan_excel
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_schedule_details_after_delete_sync_plan_excel`;

DELIMITER $$
CREATE TRIGGER `trg_schedule_details_after_delete_sync_plan_excel` AFTER DELETE ON `schedule_details` FOR EACH ROW BEGIN
  DECLARE v_machine_name VARCHAR(100);
  DECLARE v_product_cd VARCHAR(50);
  DECLARE v_order_no INT;

  SELECT m.`machine_name`, ps.`product_cd`, ps.`order_no`
    INTO v_machine_name, v_product_cd, v_order_no
  FROM `production_schedules` ps
  INNER JOIN `machines` m ON m.`id` = ps.`line_id`
  WHERE ps.`id` = OLD.`schedule_id`
  LIMIT 1;

  IF OLD.`schedule_date` IS NOT NULL
     AND v_machine_name IS NOT NULL
     AND v_product_cd IS NOT NULL THEN
    DELETE FROM `production_plan_excel`
    WHERE `日付` = OLD.`schedule_date`
      AND (`加工機` COLLATE utf8mb4_ja_0900_as_cs) = (v_machine_name COLLATE utf8mb4_ja_0900_as_cs)
      AND (`製品CD` COLLATE utf8mb4_ja_0900_as_cs) = (v_product_cd COLLATE utf8mb4_ja_0900_as_cs)
      AND (`生産順番` COLLATE utf8mb4_ja_0900_as_cs) = (CAST(LEAST(GREATEST(COALESCE(v_order_no, 0), 0), 99) AS CHAR) COLLATE utf8mb4_ja_0900_as_cs);
  END IF;
END$$
DELIMITER ;
