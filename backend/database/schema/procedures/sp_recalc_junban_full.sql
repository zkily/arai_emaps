-- PROCEDURE: sp_recalc_junban_full
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS `sp_recalc_junban_full`;

DELIMITER $$
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
END$$
DELIMITER ;
