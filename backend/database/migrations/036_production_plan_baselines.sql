-- 生産計画月次ベースライン（比較基準の固定化）
CREATE TABLE IF NOT EXISTS `production_plan_baselines` (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `baseline_month` date NOT NULL COMMENT '基準月份(每月第一天)',
  `snapshot_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '快照生成時間',
  `plan_date` date NOT NULL COMMENT '計画日',
  `machine_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '設備名',
  `product_cd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '製品名',
  `process_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '工程名',
  `plan_quantity` decimal(15, 2) NOT NULL DEFAULT 0.00 COMMENT '計画数量',
  `actual_quantity` decimal(15, 2) NOT NULL DEFAULT 0.00 COMMENT '実績数量',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uniq_baseline_month_day_proc` (`baseline_month`,`plan_date`,`process_name`) USING BTREE,
  KEY `idx_baseline_month` (`baseline_month`),
  KEY `idx_plan_date` (`plan_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生産計画月次ベースライン' ROW_FORMAT=Dynamic;
