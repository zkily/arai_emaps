-- TABLE: approval_routes
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `approval_routes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ルート名',
  `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '種類（amount:金額, department:部門, custom:カスタム）',
  `condition_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '条件タイプ',
  `condition_value` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '条件値（例: 10万円未満, 営業部）',
  `condition_min` decimal(15,2) DEFAULT NULL COMMENT '金額条件（最小）',
  `condition_max` decimal(15,2) DEFAULT NULL COMMENT '金額条件（最大）',
  `condition_department_id` int DEFAULT NULL COMMENT '部門条件',
  `priority` int DEFAULT '0' COMMENT '優先度（同条件時の判定順序）',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_approval_routes_type` (`type`),
  KEY `idx_approval_routes_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='承認ルートテーブル';

SET FOREIGN_KEY_CHECKS = 1;
