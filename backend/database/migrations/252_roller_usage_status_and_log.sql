-- ローラー使用状況（roller_usage_status）
-- ローラー使用登録（roller_usage_log）

CREATE TABLE IF NOT EXISTS `roller_usage_status` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `roller_type` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ローラー種類',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備CD',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備名',
  `exchange_freq_qty` int NULL DEFAULT NULL COMMENT '交換頻度本数',
  `exchange_freq_month` int NULL DEFAULT NULL COMMENT '交換頻度月',
  `cleaning_freq_month` int NULL DEFAULT NULL COMMENT '清掃頻度月',
  `exec_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '実施内容',
  `last_exec_date` date NULL DEFAULT NULL COMMENT '前回実施日',
  `next_exec_date` date NULL DEFAULT NULL COMMENT '次回実施日（予測）',
  `prod_cumulative_qty` int NULL DEFAULT 0 COMMENT '生産累計数（自動）',
  `prod_manual_addon_qty` int NULL DEFAULT 0 COMMENT '手入力補正（自動累計に加算）',
  `planned_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '予定段取品',
  `exchange_remaining_qty` int NULL DEFAULT NULL COMMENT '交換残数',
  `source_roller_master_updated_at` datetime NULL DEFAULT NULL COMMENT 'ローラーマスタ最終同期日時',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_roller_usage_status_roller_cd` (`roller_cd`),
  KEY `idx_roller_usage_status_machine_cd` (`machine_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラー使用状況' ROW_FORMAT=Dynamic;

CREATE TABLE IF NOT EXISTS `roller_usage_log` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `exec_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '実施内容',
  `exec_date` date NOT NULL COMMENT '実施日',
  `management_cd` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理CD',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '登録者',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_roller_usage_log_roller_cd` (`roller_cd`),
  KEY `idx_roller_usage_log_exec_date` (`exec_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラー使用登録' ROW_FORMAT=Dynamic;
