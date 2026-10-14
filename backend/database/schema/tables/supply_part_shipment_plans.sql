-- TABLE: supply_part_shipment_plans
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `supply_part_shipment_plans` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `year` int NOT NULL COMMENT '年',
  `month` int NOT NULL COMMENT '月',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `planned_date` date DEFAULT NULL COMMENT '出荷予定日',
  `is_shipped` tinyint(1) NOT NULL DEFAULT '0' COMMENT '手動出荷済',
  `shipment_txn_id` bigint DEFAULT NULL COMMENT '出荷済で作成した実出荷ID',
  `updated_by_user_id` int DEFAULT NULL COMMENT '更新者ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supply_ship_plan_month_product` (`year`,`month`,`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='補給品出荷予定日';

SET FOREIGN_KEY_CHECKS = 1;
