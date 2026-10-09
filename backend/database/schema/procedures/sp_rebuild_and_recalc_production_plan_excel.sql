-- PROCEDURE: sp_rebuild_and_recalc_production_plan_excel
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS `sp_rebuild_and_recalc_production_plan_excel`;

DELIMITER $$
CREATE PROCEDURE `sp_rebuild_and_recalc_production_plan_excel`()
BEGIN
  CALL `sp_rebuild_production_plan_excel_all`();
  CALL `sp_recalc_junban_full`();
END$$
DELIMITER ;
