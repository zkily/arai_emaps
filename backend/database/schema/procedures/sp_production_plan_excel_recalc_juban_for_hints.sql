-- PROCEDURE: sp_production_plan_excel_recalc_juban_for_hints
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS `sp_production_plan_excel_recalc_juban_for_hints`;

DELIMITER $$
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
END$$
DELIMITER ;
