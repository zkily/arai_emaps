-- TABLE: process_routes
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `process_routes` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ルートID',
  `route_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'ルートコード',
  `route_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'ルート名称',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '説明',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '使用フラグ',
  `is_default` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'デフォルトフラグ（製品に紐付く場合）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`,`route_cd`) USING BTREE,
  UNIQUE KEY `route_cd` (`route_cd`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC COMMENT='工程ルート（ヘッダ）';

SET FOREIGN_KEY_CHECKS = 1;
