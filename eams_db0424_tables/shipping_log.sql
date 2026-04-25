SET NAMES utf8mb4;

CREATE TABLE `shipping_log`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `project` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '項目',
  `date` date NULL DEFAULT NULL COMMENT '日付',
  `datetime` datetime NULL DEFAULT NULL COMMENT '日時',
  `model_no` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '機種No',
  `person_in_charge` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '担当者',
  `picking_no` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ピッキングNo',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品名',
  `product_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品CD',
  `product_name_2` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品名2',
  `quantity` int NULL DEFAULT NULL COMMENT '数量',
  `shipping_quantity` int NULL DEFAULT NULL COMMENT '出荷数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_date`(`date` ASC) USING BTREE,
  INDEX `idx_picking_no`(`picking_no` ASC) USING BTREE,
  INDEX `idx_product_code`(`product_code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3009487 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;
