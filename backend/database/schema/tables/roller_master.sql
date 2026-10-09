-- TABLE: roller_master
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `roller_master` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `roller_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ローラー名',
  `exchange_freq_qty` int DEFAULT NULL COMMENT '交換頻度本数',
  `exchange_freq_month` int DEFAULT NULL COMMENT '交換頻度月',
  `cleaning_freq_month` int DEFAULT NULL COMMENT '清掃頻度月',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '区分',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '設備CD',
  `schedule_mode` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'auto' COMMENT 'auto=自動予測, manual=手動予定日',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_roller_master_roller_cd` (`roller_cd`),
  KEY `idx_roller_master_machine_cd` (`machine_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='ローラーマスタ';

SET FOREIGN_KEY_CHECKS = 1;
