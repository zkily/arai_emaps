-- TABLE: quality_product_process_cautions
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `quality_product_process_cautions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程 cutting/chamfering/forming/welding/plating/inspection',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製品CD（NULL=工程共通）',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製品名',
  `caution_text` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '注意事項（App表示）',
  `quality_text` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品質事項（App表示）',
  `matter_kind` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'caution' COMMENT 'caution=注意事項 quality=品質事項',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '1=有効',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '並び',
  `created_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '登録者',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_qppc_process` (`process_code`,`is_active`,`sort_order`),
  KEY `idx_qppc_product` (`product_cd`,`process_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='製品生産注意事項（工程別）';

SET FOREIGN_KEY_CHECKS = 1;
