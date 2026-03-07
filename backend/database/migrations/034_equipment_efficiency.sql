-- 設備能率管理テーブル（equipment_efficiency）
-- 設備ごとの加工製品別能率設定・管理

CREATE TABLE IF NOT EXISTS `equipment_efficiency` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `machine_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備コード',
  `machines_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備名',
  `product_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品コード',
  `product_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品名',
  `efficiency_rate` decimal(10, 1) NULL DEFAULT 0.0 COMMENT '能率（数値）本/H',
  `step_time` int NULL DEFAULT NULL COMMENT '段取時間（分）',
  `unit` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '単位（例：件/時間、個/分）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `status` tinyint NULL DEFAULT NULL COMMENT '終息',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_equipment_product` (`machine_cd`, `product_cd`),
  KEY `idx_equipment_code` (`machine_cd`),
  KEY `idx_product_code` (`product_cd`),
  KEY `idx_equipment_product` (`machine_cd`, `product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備能率管理テーブル' ROW_FORMAT=Dynamic;
