-- TABLE: production_equipment_capacity
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_equipment_capacity` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_cd` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程 cutting/chamfering/forming/welding',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '設備コード',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '設備名',
  `partner_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'パートナー名',
  `vehicle_model` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '対象車種など',
  `regular_hours` decimal(6,2) NOT NULL DEFAULT '7.60' COMMENT '定時間 h/直',
  `shift_count` decimal(4,1) NOT NULL DEFAULT '2.0' COMMENT '直数',
  `overtime_hours` decimal(6,2) NOT NULL DEFAULT '0.00' COMMENT '残業 h/直',
  `working_days` decimal(5,1) NOT NULL DEFAULT '22.0' COMMENT '月間稼働日数',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '表示順',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pec_process_machine` (`process_cd`,`machine_cd`),
  KEY `idx_pec_process` (`process_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='生産設備能力ヘッダ';

SET FOREIGN_KEY_CHECKS = 1;
