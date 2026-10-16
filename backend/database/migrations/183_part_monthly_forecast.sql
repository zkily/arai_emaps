-- 部品月次内示（手入力 / 製品内示からの読込）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `part_monthly_forecast` (
  `id` int NOT NULL AUTO_INCREMENT,
  `part_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '部品CD',
  `year` int NOT NULL COMMENT '年',
  `month` tinyint NOT NULL COMMENT '月 1-12',
  `forecast_qty` int NOT NULL DEFAULT 0 COMMENT '内示数',
  `source` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'manual' COMMENT 'manual / from_product',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_part_monthly_forecast` (`part_cd`, `year`, `month`),
  KEY `idx_part_monthly_forecast_year` (`year`, `month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部品月次内示';
