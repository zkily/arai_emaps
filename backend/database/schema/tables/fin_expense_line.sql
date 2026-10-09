-- TABLE: fin_expense_line
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_expense_line` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `application_id` bigint NOT NULL COMMENT '親レコードID',
  `line_no` int DEFAULT '1' COMMENT '行番号',
  `expense_date` date DEFAULT NULL COMMENT '利用日',
  `category_code` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '経費区分',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '摘要',
  `amount` decimal(18,2) DEFAULT '0.00' COMMENT '金額',
  `tax_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '税区分コード',
  `has_receipt` tinyint(1) DEFAULT '0' COMMENT '領収書添付フラグ',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_expense_line_application_id` (`application_id`),
  CONSTRAINT `fk_fin_expense_line_application_id` FOREIGN KEY (`application_id`) REFERENCES `fin_expense_application` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='経費明細';

SET FOREIGN_KEY_CHECKS = 1;
