-- TABLE: material_usage_record
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `material_usage_record` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `usage_date` date NOT NULL COMMENT '使用日（生産日）',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料CD（materials テーブル参照）',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料名（冗長保持）',
  `usage_count` decimal(10,4) NOT NULL DEFAULT '1.0000' COMMENT '使用数（行の usage_count をそのまま、按分時は <1）',
  `source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'cutting' COMMENT '来源区分（cutting / chamfering など）',
  `management_codes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '管理コード（複数はカンマ区切り）',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '管理コード（単一、cutting_management.management_code に対応）',
  `reflected` tinyint(1) NOT NULL DEFAULT '0' COMMENT '反映済（0=未反映, 1=反映済）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_management_code_source` (`management_code`,`source`),
  KEY `idx_usage_date` (`usage_date`),
  KEY `idx_material_cd` (`material_cd`),
  KEY `idx_source` (`source`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='材料使用済テーブル（切断工程等の日次材料使用数を管理）';

SET FOREIGN_KEY_CHECKS = 1;
