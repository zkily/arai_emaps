-- TABLE: material_logs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `material_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目/品种标识',
  `log_date` date NOT NULL COMMENT '日志日期',
  `log_time` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '日志时间',
  `hd_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'HD No',
  `remarks` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `material_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `manufacture_no` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製造番号',
  `manufacture_date` date DEFAULT NULL,
  `pieces_per_bundle` int DEFAULT NULL,
  `length` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `bundle_quantity` int DEFAULT NULL,
  `magnetic` tinyint DEFAULT '1',
  `appearance` tinyint DEFAULT '1',
  `outer_diameter1` decimal(12,4) DEFAULT NULL,
  `outer_diameter2` decimal(12,4) DEFAULT NULL,
  `supplier` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `material_quality` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `note` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cutting_used_manual` tinyint(1) NOT NULL DEFAULT '0' COMMENT '手動で切断使用済と確定',
  `cutting_used_manual_at` datetime DEFAULT NULL COMMENT '手動確定日時',
  `cutting_used_manual_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手動確定ユーザー',
  `cutting_used_manual_note` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手動確定理由・備考',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_item` (`item`),
  KEY `idx_log_date` (`log_date`),
  KEY `idx_manufacture` (`manufacture_no`,`log_date`,`log_time`),
  KEY `idx_material_logs_cutting_used_manual` (`cutting_used_manual`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='材料检收日志(BT-data受信)';

SET FOREIGN_KEY_CHECKS = 1;
