-- ローラーBOM（roller_bom）
-- ローラーマスタ（roller_master）

CREATE TABLE IF NOT EXISTS `roller_bom` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `roller_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ローラー種類',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '設備CD',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_roller_bom_roller_cd` (`roller_cd`),
  KEY `idx_roller_bom_product_cd` (`product_cd`),
  KEY `idx_roller_bom_machine_cd` (`machine_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラーBOM' ROW_FORMAT=Dynamic;

CREATE TABLE IF NOT EXISTS `roller_master` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `roller_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ローラー名',
  `exchange_freq_qty` int NULL DEFAULT NULL COMMENT '交換頻度本数',
  `exchange_freq_month` int NULL DEFAULT NULL COMMENT '交換頻度月',
  `cleaning_freq_month` int NULL DEFAULT NULL COMMENT '清掃頻度月',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '区分',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備CD',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_roller_master_roller_cd` (`roller_cd`),
  KEY `idx_roller_master_machine_cd` (`machine_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラーマスタ' ROW_FORMAT=Dynamic;
