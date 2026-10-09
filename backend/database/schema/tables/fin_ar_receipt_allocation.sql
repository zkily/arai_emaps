-- TABLE: fin_ar_receipt_allocation
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_ar_receipt_allocation` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `receipt_id` bigint NOT NULL COMMENT '親レコードID',
  `invoice_id` bigint DEFAULT NULL COMMENT '消込対象請求',
  `allocated_amount` decimal(18,2) DEFAULT '0.00' COMMENT '充当額',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_ar_receipt_allocation_receipt_id` (`receipt_id`),
  KEY `idx_fin_ar_receipt_allocation_invoice_id` (`invoice_id`),
  CONSTRAINT `fk_fin_ar_receipt_allocation_receipt_id` FOREIGN KEY (`receipt_id`) REFERENCES `fin_ar_receipt` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='入金消込';

SET FOREIGN_KEY_CHECKS = 1;
