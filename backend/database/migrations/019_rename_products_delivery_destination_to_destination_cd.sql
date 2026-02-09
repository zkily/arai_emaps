-- products.delivery_destination_cd を destination_cd にリネーム（既存DB用）
SET NAMES utf8mb4;

ALTER TABLE `products`
  CHANGE COLUMN `delivery_destination_cd` `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '納入先CD（外部キー）';
