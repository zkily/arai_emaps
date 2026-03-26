-- production_schedules に product_cd カラム追加

ALTER TABLE `production_schedules`
  ADD COLUMN `product_cd` VARCHAR(50) NULL DEFAULT NULL COMMENT '製品コード' AFTER `item_name`;

CREATE INDEX `idx_ps_product_cd` ON `production_schedules` (`product_cd`);
