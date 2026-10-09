-- TABLE: production_review_meetings
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_review_meetings` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `target_month` varchar(7) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '対象月 YYYY-MM',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft' COMMENT 'draft/final',
  `data_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ページデータJSON',
  `generated_at` datetime DEFAULT NULL COMMENT '最終集計日時',
  `created_by_user_id` int DEFAULT NULL COMMENT '作成者ID',
  `updated_by_user_id` int DEFAULT NULL COMMENT '更新者ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_prm_target_month` (`target_month`),
  KEY `idx_prm_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='生産検討会資料（月次）';

SET FOREIGN_KEY_CHECKS = 1;
