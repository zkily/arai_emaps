-- PROCEDURE: sp_rebuild_production_plan_excel_all
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS `sp_rebuild_production_plan_excel_all`;

DELIMITER $$
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
END$$
DELIMITER ;
