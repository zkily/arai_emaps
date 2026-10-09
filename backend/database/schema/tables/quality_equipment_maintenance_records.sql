-- TABLE: quality_equipment_maintenance_records
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `quality_equipment_maintenance_records` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `equipment_id` bigint NOT NULL COMMENT '設備ID',
  `work_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'maintenance=保全 repair=修理',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'planned' COMMENT 'planned/done/cancelled',
  `planned_date` date DEFAULT NULL COMMENT '予定日',
  `actual_date` date DEFAULT NULL COMMENT '実施日',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '件名',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '内容',
  `assignee` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '担当',
  `work_hours` decimal(8,2) DEFAULT NULL COMMENT '工数(H)',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '登録者',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_qemr_equipment` (`equipment_id`,`status`),
  KEY `idx_qemr_planned` (`planned_date`),
  KEY `idx_qemr_actual` (`actual_date`),
  CONSTRAINT `fk_qemr_equipment` FOREIGN KEY (`equipment_id`) REFERENCES `quality_equipment_maintenance` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備保全 実績・予定';

SET FOREIGN_KEY_CHECKS = 1;
