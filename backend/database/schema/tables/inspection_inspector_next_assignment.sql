-- TABLE: inspection_inspector_next_assignment
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inspection_inspector_next_assignment` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `production_day` date NOT NULL COMMENT '生産日',
  `inspector_user_id` int NOT NULL COMMENT '検査員 users.id',
  `next_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '次製品CD',
  `next_product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '次製品名',
  `assigned_by_user_id` int DEFAULT NULL COMMENT '指定者 users.id',
  `assigned_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '指定日時',
  `note` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備考',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_day_inspector` (`production_day`,`inspector_user_id`),
  KEY `idx_production_day` (`production_day`),
  KEY `idx_inspector_user_id` (`inspector_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='検査員次製品指定';

SET FOREIGN_KEY_CHECKS = 1;
