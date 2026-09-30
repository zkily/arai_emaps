-- 部品マスタ：部品材料（使用材料の自由入力、例：SUS304 / S45C）
SET NAMES utf8mb4;

ALTER TABLE `parts`
  ADD COLUMN `part_material` VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL
    COMMENT '部品材料（使用材料）'
  AFTER `category`;
