-- TABLE: fin_ap_payment_allocation
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_ap_payment_allocation` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `payment_id` bigint NOT NULL COMMENT '親レコードID',
  `bill_id` bigint DEFAULT NULL COMMENT '消込対象仕入請求',
  `allocated_amount` decimal(18,2) DEFAULT '0.00' COMMENT '充当金額',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_ap_payment_allocation_payment_id` (`payment_id`),
  KEY `idx_fin_ap_payment_allocation_bill_id` (`bill_id`),
  CONSTRAINT `fk_fin_ap_payment_allocation_payment_id` FOREIGN KEY (`payment_id`) REFERENCES `fin_ap_payment` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='支払消込';

SET FOREIGN_KEY_CHECKS = 1;
