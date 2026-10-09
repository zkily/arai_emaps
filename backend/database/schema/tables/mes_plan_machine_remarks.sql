-- TABLE: mes_plan_machine_remarks
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `mes_plan_machine_remarks` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_name` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '成型' COMMENT '工程（成型/溶接）',
  `plan_date` date NOT NULL COMMENT '生産日',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '設備名',
  `remarks` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '手入力備考',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_mes_plan_machine_remarks` (`process_name`,`plan_date`,`machine_name`),
  KEY `idx_mes_plan_machine_remarks_date` (`process_name`,`plan_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='MES計画 設備名×生産日 手入力備考';

SET FOREIGN_KEY_CHECKS = 1;
