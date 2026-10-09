-- TABLE: workflow_definitions
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `workflow_definitions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ワークフローコード（例: WF_PO）',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ワークフロー名',
  `document_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '対象伝票タイプ',
  `approval_route_id` int DEFAULT NULL COMMENT 'デフォルト承認ルートID',
  `timeout_days` int DEFAULT '3' COMMENT '承認期限（日数）',
  `escalation_enabled` tinyint(1) DEFAULT '0' COMMENT 'エスカレーション有効',
  `escalation_days` int DEFAULT NULL COMMENT 'エスカレーションまでの日数',
  `escalation_target` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'エスカレーション先',
  `auto_approve_enabled` tinyint(1) DEFAULT '0' COMMENT '自動承認有効',
  `auto_approve_condition` json DEFAULT NULL COMMENT '自動承認条件',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `idx_workflow_defs_code` (`code`),
  KEY `idx_workflow_defs_doctype` (`document_type`),
  KEY `fk_workflow_defs_route` (`approval_route_id`),
  CONSTRAINT `fk_workflow_defs_route` FOREIGN KEY (`approval_route_id`) REFERENCES `approval_routes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ワークフロー定義テーブル';

SET FOREIGN_KEY_CHECKS = 1;
