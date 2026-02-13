-- 納入先分组管理表（出荷構成表等で使用）
-- 既にテーブルがある場合はスキップ（DROP しない）
CREATE TABLE IF NOT EXISTS `destination_groups` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键，自增',
  `page_key` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '页面唯一标识，用于区分不同页面的分组集合',
  `group_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分组名称，用户自定义',
  `destinations` json NOT NULL COMMENT '分组内的纳入先列表，JSON格式存储',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间戳',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间戳',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_page_key`(`page_key` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='納入先分组管理表' ROW_FORMAT=Dynamic;
