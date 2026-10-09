-- TABLE: process_defect_items
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `process_defect_items` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `detection_process_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '収集・表示工程CD（MES画面の工程）',
  `attributable_process_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '帰属工程CD（不良を負う工程）',
  `defect_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '不良項目CD（mes_defect_by_item等のキー）',
  `defect_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '不良項目名',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '表示順',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT 'active / inactive',
  `remarks` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pdi_detection_defect_cd` (`detection_process_cd`,`defect_cd`),
  KEY `idx_pdi_detection` (`detection_process_cd`),
  KEY `idx_pdi_attributable` (`attributable_process_cd`),
  KEY `idx_pdi_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='工程別不良項目マスタ';

SET FOREIGN_KEY_CHECKS = 1;
