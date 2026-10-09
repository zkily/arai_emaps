-- EVENT: evt_production_plan_excel_juban_recalc
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

DROP EVENT IF EXISTS `evt_production_plan_excel_juban_recalc`;

DELIMITER $$
CREATE EVENT `evt_production_plan_excel_juban_recalc` ON SCHEDULE EVERY 5 SECOND STARTS '2026-10-09 08:34:14' ON COMPLETION PRESERVE ENABLE COMMENT '消费 juban_recalc_hint，重算各组 順番（需 event_scheduler=ON）' DO BEGIN
  IF EXISTS (SELECT 1 FROM `production_plan_excel_juban_recalc_hint` LIMIT 1) THEN
    CALL `sp_production_plan_excel_recalc_juban_for_hints`();
  END IF;
END$$
DELIMITER ;
