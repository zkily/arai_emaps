-- product_label_config.product_cd を products と同じ collation に揃える
SET NAMES utf8mb4;

ALTER TABLE `product_label_config`
  MODIFY COLUMN `product_cd` VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD';
