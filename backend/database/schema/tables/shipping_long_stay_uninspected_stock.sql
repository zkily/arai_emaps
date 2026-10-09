-- TABLE: shipping_long_stay_uninspected_stock
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `shipping_long_stay_uninspected_stock` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `quantity` int NOT NULL DEFAULT '0' COMMENT '本数',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '表示順',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_slsus_sort` (`sort_order`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='長期滞在未検査在庫（不足数印刷備考）';

SET FOREIGN_KEY_CHECKS = 1;
