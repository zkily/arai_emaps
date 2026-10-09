-- TABLE: line_product_standard
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `line_product_standard` (
  `id` int NOT NULL AUTO_INCREMENT,
  `line_id` int NOT NULL COMMENT '産線ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品コード',
  `std_qty_per_hour` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '小時あたり標準産出量',
  `setup_time_min` int NOT NULL DEFAULT '0' COMMENT '段取時間（分）',
  `efficiency_pct` decimal(5,2) NOT NULL DEFAULT '100.00' COMMENT '標準能率（%）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_line_product` (`line_id`,`product_cd`),
  KEY `idx_lps_product` (`product_cd`),
  CONSTRAINT `fk_lps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線×製品 標準工時マスタ';

SET FOREIGN_KEY_CHECKS = 1;
