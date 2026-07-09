-- 区分（社内/外注）
SET NAMES utf8mb4;

ALTER TABLE `product_label_config`
  ADD COLUMN `supply_type` VARCHAR(10) NOT NULL DEFAULT '社内'
  COMMENT '区分（社内/外注）'
  AFTER `upper_slots_locked`;
