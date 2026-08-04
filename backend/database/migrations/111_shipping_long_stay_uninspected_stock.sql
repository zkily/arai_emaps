-- 出荷不足数一覧印刷 備考：長期滞在未検査在庫
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `shipping_long_stay_uninspected_stock` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `quantity` int NOT NULL DEFAULT 0 COMMENT '本数',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '表示順',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_slsus_sort` (`sort_order`, `id`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '長期滞在未検査在庫（不足数印刷備考）' ROW_FORMAT = Dynamic;
