-- TABLE: destination_groups
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `destination_groups` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键，自增',
  `page_key` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '页面唯一标识，用于区分不同页面的分组集合',
  `group_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分组名称，用户自定义',
  `destinations` json NOT NULL COMMENT '分组内的纳入先列表，JSON格式存储',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间戳',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间戳',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_page_key` (`page_key`) USING BTREE,
  KEY `idx_updated_at` (`updated_at`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='納入先分组管理表';

SET FOREIGN_KEY_CHECKS = 1;
