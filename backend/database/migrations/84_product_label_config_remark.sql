-- 備考（現品票印字用）
SET NAMES utf8mb4;

ALTER TABLE `product_label_config`
  ADD COLUMN `remark` VARCHAR(255) NULL DEFAULT NULL
  COMMENT '備考'
  AFTER `supply_type`;
