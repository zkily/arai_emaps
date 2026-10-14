-- 補給品 出荷予定日（対象月・製品ごと。画面から手修正）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `supply_part_shipment_plans` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `year` int NOT NULL COMMENT '年',
  `month` int NOT NULL COMMENT '月',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `planned_date` date NULL DEFAULT NULL COMMENT '出荷予定日',
  `updated_by_user_id` int NULL DEFAULT NULL COMMENT '更新者ID',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supply_ship_plan_month_product` (`year`, `month`, `product_cd`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '補給品出荷予定日' ROW_FORMAT = Dynamic;
