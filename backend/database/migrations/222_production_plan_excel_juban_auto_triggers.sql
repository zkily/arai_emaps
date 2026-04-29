-- production_plan_excel: 按 日付+加工機 分组，按 生産順番 升序（id 作 tie-break）写入 順番（仅 1/2）
-- 规则：每组第 1 条写 1；第 2 条及以后统一写 2。
-- MySQL 禁止在本表触发器里再次 UPDATE 本表，因此：触发器只写入提示表，由存储过程（或定时 EVENT）执行重算。
-- 依赖：表 production_plan_excel 已存在且含列 日付、加工機、生産順番、順番；MySQL 8.0+（需窗口函数 ROW_NUMBER）。

CREATE TABLE IF NOT EXISTS `production_plan_excel_juban_recalc_hint` (
  `日付` date NOT NULL,
  `加工機` varchar(50) NOT NULL,
  `queued_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`日付`, `加工機`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_ja_0900_as_cs COMMENT = 'production_plan_excel 順番重算队列';

DELIMITER $$

DROP PROCEDURE IF EXISTS `sp_production_plan_excel_recalc_juban_for_hints` $$
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
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_excel_after_insert_juban` $$
CREATE TRIGGER `trg_production_plan_excel_after_insert_juban`
AFTER INSERT ON `production_plan_excel`
FOR EACH ROW
BEGIN
  INSERT IGNORE INTO `production_plan_excel_juban_recalc_hint` (`日付`, `加工機`)
  VALUES (NEW.`日付`, NEW.`加工機`);
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_excel_after_update_juban` $$
CREATE TRIGGER `trg_production_plan_excel_after_update_juban`
AFTER UPDATE ON `production_plan_excel`
FOR EACH ROW
BEGIN
  INSERT IGNORE INTO `production_plan_excel_juban_recalc_hint` (`日付`, `加工機`)
  VALUES (OLD.`日付`, OLD.`加工機`);
  IF NEW.`日付` <> OLD.`日付` OR NEW.`加工機` <> OLD.`加工機` THEN
    INSERT IGNORE INTO `production_plan_excel_juban_recalc_hint` (`日付`, `加工機`)
    VALUES (NEW.`日付`, NEW.`加工機`);
  END IF;
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_excel_after_delete_juban` $$
CREATE TRIGGER `trg_production_plan_excel_after_delete_juban`
AFTER DELETE ON `production_plan_excel`
FOR EACH ROW
BEGIN
  INSERT IGNORE INTO `production_plan_excel_juban_recalc_hint` (`日付`, `加工機`)
  VALUES (OLD.`日付`, OLD.`加工機`);
END $$

DROP EVENT IF EXISTS `evt_production_plan_excel_juban_recalc` $$
CREATE EVENT `evt_production_plan_excel_juban_recalc`
ON SCHEDULE EVERY 5 SECOND
STARTS CURRENT_TIMESTAMP
ON COMPLETION PRESERVE
ENABLE
COMMENT '消费 juban_recalc_hint，重算各组 順番（需 event_scheduler=ON）'
DO
BEGIN
  IF EXISTS (SELECT 1 FROM `production_plan_excel_juban_recalc_hint` LIMIT 1) THEN
    CALL `sp_production_plan_excel_recalc_juban_for_hints`();
  END IF;
END $$

DELIMITER ;

-- 若 EVENT 不执行，请确认：SET GLOBAL event_scheduler = ON;
-- 也可在应用侧在批量写入后执行：CALL sp_production_plan_excel_recalc_juban_for_hints();
