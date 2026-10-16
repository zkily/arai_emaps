-- 部品マスタ：別名
SET NAMES utf8mb4;

ALTER TABLE `parts`
  ADD COLUMN `alias_name` VARCHAR(200) DEFAULT NULL COMMENT '別名'
  AFTER `part_name`;
