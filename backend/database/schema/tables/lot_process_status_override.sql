-- TABLE: lot_process_status_override
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `lot_process_status_override` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '管理コード',
  `aps_batch_plan_id` int DEFAULT NULL COMMENT '参照用 APS批次ID',
  `cutting_completed` tinyint(1) DEFAULT NULL COMMENT '切断完了（NULL=自動判定）',
  `molding_completed` tinyint(1) DEFAULT NULL COMMENT '成型完了（NULL=自動判定）',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備考',
  `updated_by` int DEFAULT NULL COMMENT '更新者 users.id',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_lpso_management_code` (`management_code`),
  KEY `idx_lpso_aps_batch_plan_id` (`aps_batch_plan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='ロット進捗状態手動指定';

SET FOREIGN_KEY_CHECKS = 1;
