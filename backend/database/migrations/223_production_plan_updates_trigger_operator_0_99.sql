-- schedule_details(+production_schedules/machines) -> production_plan_excel 同步触发器
-- 目标：所有设备都可写入（不再限制 machine_type='成型'）
-- 说明：
--   1) 生産順番 使用 production_schedules.order_no，空值按 0，越界按 0~99 截断
--   2) 使用 INSERT ... ON DUPLICATE KEY UPDATE，避免重复键导致写入失败
--   3) 触发器内不抛 SIGNAL，避免业务事务整体回滚

DELIMITER $$

DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_insert` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_update` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_delete` $$

DROP TRIGGER IF EXISTS `trg_schedule_details_after_insert_sync_plan_excel` $$
CREATE TRIGGER `trg_schedule_details_after_insert_sync_plan_excel`
AFTER INSERT ON `schedule_details`
FOR EACH ROW
BEGIN
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
END $$

DROP TRIGGER IF EXISTS `trg_schedule_details_after_update_sync_plan_excel` $$
CREATE TRIGGER `trg_schedule_details_after_update_sync_plan_excel`
AFTER UPDATE ON `schedule_details`
FOR EACH ROW
BEGIN
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
END $$

DROP TRIGGER IF EXISTS `trg_schedule_details_after_delete_sync_plan_excel` $$
CREATE TRIGGER `trg_schedule_details_after_delete_sync_plan_excel`
AFTER DELETE ON `schedule_details`
FOR EACH ROW
BEGIN
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
END $$

DROP TRIGGER IF EXISTS `trg_production_schedules_after_update_sync_plan_excel` $$
CREATE TRIGGER `trg_production_schedules_after_update_sync_plan_excel`
AFTER UPDATE ON `production_schedules`
FOR EACH ROW
BEGIN
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
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_insert` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_update` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_delete` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_insert_legacy` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_update_legacy` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_delete_legacy` $$

DELIMITER ;
