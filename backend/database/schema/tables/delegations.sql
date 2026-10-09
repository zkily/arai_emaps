-- TABLE: delegations
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `delegations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `delegator_id` int NOT NULL COMMENT '委任者ユーザーID',
  `delegate_id` int NOT NULL COMMENT '代理者ユーザーID',
  `start_date` date NOT NULL COMMENT '開始日',
  `end_date` date NOT NULL COMMENT '終了日',
  `scope` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'all' COMMENT '範囲（all:全承認, specific:特定）',
  `scope_details` json DEFAULT NULL COMMENT '範囲詳細（特定の場合）',
  `reason` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '理由',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT 'ステータス（active/expired/cancelled）',
  `created_by` int DEFAULT NULL COMMENT '作成者',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_delegations_delegator` (`delegator_id`),
  KEY `idx_delegations_delegate` (`delegate_id`),
  KEY `idx_delegations_dates` (`start_date`,`end_date`),
  KEY `idx_delegations_status` (`status`),
  CONSTRAINT `fk_delegations_delegate` FOREIGN KEY (`delegate_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_delegations_delegator` FOREIGN KEY (`delegator_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代理承認テーブル';

SET FOREIGN_KEY_CHECKS = 1;
