-- TABLE: fin_withholding_tax_table
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_withholding_tax_table` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '税表バージョン',
  `min_amount` decimal(18,2) DEFAULT '0.00' COMMENT '下限',
  `max_amount` decimal(18,2) DEFAULT NULL COMMENT '上限',
  `dependents` int DEFAULT '0' COMMENT '扶養人数',
  `tax_amount` decimal(18,2) DEFAULT '0.00' COMMENT '源泉税額',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_withholding_tax_table_version` (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='源泉徴収税額表';

SET FOREIGN_KEY_CHECKS = 1;
