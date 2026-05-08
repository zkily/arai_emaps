-- production_plan_updates.quantity を production_summarys.molding_actual_plan へ反映
-- 条件: production_plan_updates.plan_date < '2026-03-01'
-- 紐付け: plan_date = date, product_cd = product_cd

UPDATE `production_summarys` AS ps
INNER JOIN (
  SELECT
    `plan_date`,
    `product_cd`,
    SUM(COALESCE(`quantity`, 0)) AS `quantity_sum`
  FROM `production_plan_updates`
  WHERE `plan_date` < '2026-03-01'
  GROUP BY `plan_date`, `product_cd`
) AS ppu
  ON ppu.`plan_date` = ps.`date`
 AND ppu.`product_cd` = ps.`product_cd`
SET ps.`molding_actual_plan` = ppu.`quantity_sum`
WHERE ps.`date` < '2026-03-01';
