-- 部品マスタ：収容数（1容器あたりの収容数量）
SET NAMES utf8mb4;

ALTER TABLE `parts`
  ADD COLUMN `capacity_qty` INT DEFAULT NULL COMMENT '収容数'
  AFTER `uom`;
