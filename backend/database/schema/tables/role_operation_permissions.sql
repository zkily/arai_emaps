-- TABLE: role_operation_permissions
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `role_operation_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_id` int NOT NULL COMMENT 'ロールID',
  `module` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'モジュール名',
  `can_create` tinyint(1) DEFAULT '0' COMMENT '新規作成権限',
  `can_edit` tinyint(1) DEFAULT '0' COMMENT '編集権限',
  `can_delete` tinyint(1) DEFAULT '0' COMMENT '削除権限',
  `can_export` tinyint(1) DEFAULT '0' COMMENT '出力権限',
  `can_approve` tinyint(1) DEFAULT '0' COMMENT '承認権限',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_module` (`role_id`,`module`),
  KEY `idx_rop_role` (`role_id`),
  CONSTRAINT `fk_rop_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ロール・操作権限テーブル';

SET FOREIGN_KEY_CHECKS = 1;
