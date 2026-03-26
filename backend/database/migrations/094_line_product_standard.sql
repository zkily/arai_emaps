-- 産線×製品 標準工時マスタ
-- 製品ごとの産線における小時産能・段取時間・能率を管理

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `line_product_standard` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT '産線ID',
  `product_cd` VARCHAR(50) NOT NULL COMMENT '製品コード',
  `std_qty_per_hour` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '小時あたり標準産出量',
  `setup_time_min` INT NOT NULL DEFAULT 0 COMMENT '段取時間（分）',
  `efficiency_pct` DECIMAL(5,2) NOT NULL DEFAULT 100.00 COMMENT '標準能率（%）',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_line_product` (`line_id`, `product_cd`),
  INDEX `idx_lps_product` (`product_cd`),
  CONSTRAINT `fk_lps_line` FOREIGN KEY (`line_id`) REFERENCES `production_lines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線×製品 標準工時マスタ';

SET FOREIGN_KEY_CHECKS = 1;
