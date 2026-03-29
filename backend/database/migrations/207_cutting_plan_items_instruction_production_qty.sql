-- cutting_plan_items: 指示計画の生産数（instruction_plans.actual_production_quantity）を保持し一覧表示用にする

ALTER TABLE `cutting_plan_items`
  ADD COLUMN `instruction_production_quantity` int NOT NULL DEFAULT 0 COMMENT '指示計画の生産数' AFTER `planned_quantity`;

UPDATE `cutting_plan_items` cpi
INNER JOIN `instruction_plans` ip ON cpi.instruction_plan_id = ip.id
SET cpi.instruction_production_quantity = COALESCE(ip.actual_production_quantity, 0)
WHERE cpi.instruction_plan_id IS NOT NULL;
