-- production_plan_updates -> production_plan_excel 同步触发器
-- 将 operator（varchar）映射到 生産順番（0～99），兼容两位数规则
-- 说明：旧库中若存在“operator 必须为 1 或 2”触发器，会被此迁移覆盖

DELIMITER $$

DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_insert` $$
CREATE TRIGGER `trg_production_plan_updates_after_insert`
AFTER INSERT ON `production_plan_updates`
FOR EACH ROW
BEGIN
  IF NEW.`plan_date` IS NULL OR NEW.`machine_name` IS NULL
     OR NEW.`product_cd` IS NULL OR NEW.`product_name` IS NULL
     OR NEW.`quantity` IS NULL OR NEW.`operator` IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'production_plan_updates: plan_date/machine_name/product_cd/product_name/quantity/operator 不能为空';
  END IF;

  IF NEW.`operator` NOT REGEXP '^[0-9]{1,2}$' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'operator 必须是 0~99 的数字（1~2位）';
  END IF;

  INSERT INTO `production_plan_excel` (
    `日付`, `加工機`, `製品CD`, `製品名`, `加工計画`, `生産順番`
  ) VALUES (
    NEW.`plan_date`,
    NEW.`machine_name`,
    NEW.`product_cd`,
    NEW.`product_name`,
    NEW.`quantity`,
    CAST(NEW.`operator` AS UNSIGNED)
  );
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_update` $$
CREATE TRIGGER `trg_production_plan_updates_after_update`
AFTER UPDATE ON `production_plan_updates`
FOR EACH ROW
BEGIN
  IF NEW.`plan_date` IS NULL OR NEW.`machine_name` IS NULL
     OR NEW.`product_cd` IS NULL OR NEW.`product_name` IS NULL
     OR NEW.`quantity` IS NULL OR NEW.`operator` IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'production_plan_updates: plan_date/machine_name/product_cd/product_name/quantity/operator 不能为空';
  END IF;

  IF NEW.`operator` NOT REGEXP '^[0-9]{1,2}$' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'operator 必须是 0~99 的数字（1~2位）';
  END IF;

  UPDATE `production_plan_excel`
  SET
    `日付`     = NEW.`plan_date`,
    `加工機`   = NEW.`machine_name`,
    `製品CD`   = NEW.`product_cd`,
    `製品名`   = NEW.`product_name`,
    `加工計画` = NEW.`quantity`,
    `生産順番` = CAST(NEW.`operator` AS UNSIGNED)
  WHERE `日付`     <=> OLD.`plan_date`
    AND `加工機`   <=> OLD.`machine_name`
    AND `製品CD`   <=> OLD.`product_cd`
    AND `生産順番` <=> CAST(OLD.`operator` AS UNSIGNED);
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_delete` $$
CREATE TRIGGER `trg_production_plan_updates_after_delete`
AFTER DELETE ON `production_plan_updates`
FOR EACH ROW
BEGIN
  DELETE FROM `production_plan_excel`
  WHERE `日付`     <=> OLD.`plan_date`
    AND `加工機`   <=> OLD.`machine_name`
    AND `製品CD`   <=> OLD.`product_cd`
    AND `生産順番` <=> CAST(OLD.`operator` AS UNSIGNED);
END $$

DELIMITER ;
