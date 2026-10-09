-- TABLE: aps_plating_plan_draft_items
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `aps_plating_plan_draft_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `draft_id` int NOT NULL,
  `sort_order` int NOT NULL DEFAULT '0',
  `work_date` date DEFAULT NULL,
  `product_cd` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `plating_machine` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `kake` decimal(10,2) NOT NULL DEFAULT '0.00',
  `qty` int NOT NULL DEFAULT '0',
  `slots` int NOT NULL DEFAULT '0',
  `source_type` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_row_key` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_aps_plating_plan_draft_items_draft_sort` (`draft_id`,`sort_order`),
  KEY `idx_aps_plating_plan_draft_items_product_cd` (`product_cd`),
  KEY `idx_aps_plating_plan_draft_items_work_date` (`work_date`),
  CONSTRAINT `fk_aps_plating_plan_draft_items_draft` FOREIGN KEY (`draft_id`) REFERENCES `aps_plating_plan_drafts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
