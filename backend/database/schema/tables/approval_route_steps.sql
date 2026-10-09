-- TABLE: approval_route_steps
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `approval_route_steps` (
  `id` int NOT NULL AUTO_INCREMENT,
  `route_id` int NOT NULL COMMENT '承認ルートID',
  `step_order` int NOT NULL COMMENT 'ステップ順序（1から開始）',
  `step_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ステップ名（例: 課長）',
  `approver_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '承認者タイプ（role:ロール, user:特定ユーザー, position:役職）',
  `approver_id` int DEFAULT NULL COMMENT '承認者ID（ユーザーID or ロールID）',
  `approver_position` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '役職名',
  `is_optional` tinyint(1) DEFAULT '0' COMMENT 'スキップ可能フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_route_steps_route` (`route_id`),
  KEY `idx_route_steps_order` (`route_id`,`step_order`),
  CONSTRAINT `fk_route_steps_route` FOREIGN KEY (`route_id`) REFERENCES `approval_routes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='承認ルートステップテーブル';

SET FOREIGN_KEY_CHECKS = 1;
