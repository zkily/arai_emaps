-- TABLE: shipping_pallet_advance_tohoku
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `shipping_pallet_advance_tohoku` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `advance_date` date NOT NULL COMMENT '先出を計上する積込日',
  `qty` int NOT NULL DEFAULT '0' COMMENT '先出パレット数',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_spat_advance_date` (`advance_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='出荷パレット数 先出(東北)';

SET FOREIGN_KEY_CHECKS = 1;
