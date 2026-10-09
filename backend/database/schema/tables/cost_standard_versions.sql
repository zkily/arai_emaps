-- TABLE: cost_standard_versions
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `cost_standard_versions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '表示コード（例 FY2026-A）',
  `fiscal_year` int NOT NULL COMMENT '会計年度',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft' COMMENT 'draft/active/archived',
  `effective_from` date NOT NULL COMMENT '適用開始日',
  `effective_to` date DEFAULT NULL COMMENT '適用終了日（NULL=無期限）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_csv_code` (`code`),
  KEY `idx_csv_year_status` (`fiscal_year`,`status`),
  KEY `idx_csv_effective` (`effective_from`,`effective_to`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価バージョン';

SET FOREIGN_KEY_CHECKS = 1;
