-- TABLE: budget_monthly
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `budget_monthly` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `year` smallint NOT NULL COMMENT '年',
  `month` tinyint NOT NULL COMMENT '月',
  `development_code` varchar(100) DEFAULT NULL COMMENT '開発コード',
  `part_number` varchar(50) NOT NULL COMMENT '品番（CSV）',
  `product_cd` varchar(50) DEFAULT NULL COMMENT '製品CD（末尾1のみ紐付）',
  `product_name` varchar(100) DEFAULT NULL COMMENT '製品名',
  `budget_qty` int NOT NULL DEFAULT '0' COMMENT '予算数量',
  `match_status` varchar(20) NOT NULL DEFAULT 'unmatched' COMMENT 'matched|unmatched|multi_match',
  `import_batch_id` bigint DEFAULT NULL,
  `source_file_name` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_budget_ym_part` (`year`,`month`,`part_number`),
  KEY `idx_budget_ym` (`year`,`month`),
  KEY `idx_budget_product_cd` (`product_cd`),
  KEY `idx_budget_part_number` (`part_number`),
  KEY `idx_budget_batch` (`import_batch_id`),
  CONSTRAINT `fk_budget_monthly_batch` FOREIGN KEY (`import_batch_id`) REFERENCES `budget_import_batches` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='月次予算数量（同月同品番は上書き）';

SET FOREIGN_KEY_CHECKS = 1;
