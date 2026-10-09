-- EVENT: evt_production_plan_excel_nightly_rebuild
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP EVENT IF EXISTS `evt_production_plan_excel_nightly_rebuild`;

DELIMITER $$
CREATE EVENT `evt_production_plan_excel_nightly_rebuild` ON SCHEDULE EVERY 1 DAY STARTS '2026-04-29 02:30:00' ON COMPLETION PRESERVE ENABLE COMMENT 'Nightly rebuild + junban recalc for production_plan_excel' DO BEGIN
  CALL `sp_rebuild_and_recalc_production_plan_excel`();
END$$
DELIMITER ;
