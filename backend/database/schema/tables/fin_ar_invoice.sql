-- TABLE: fin_ar_invoice
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_ar_invoice` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `invoice_no` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '請求番号',
  `partner_id` int DEFAULT NULL COMMENT '取引先',
  `partner_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '取引先名',
  `invoice_date` date NOT NULL COMMENT '請求日',
  `due_date` date DEFAULT NULL COMMENT '支払期限',
  `subtotal` decimal(18,2) DEFAULT '0.00' COMMENT '税抜',
  `tax_amount` decimal(18,2) DEFAULT '0.00' COMMENT '消費税',
  `total_amount` decimal(18,2) DEFAULT '0.00' COMMENT '税込合計',
  `paid_amount` decimal(18,2) DEFAULT '0.00' COMMENT '入金済',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'draft' COMMENT '状態（下書き/発行済/入金済/延滞）',
  `source_invoice_id` int DEFAULT NULL COMMENT 'ERP 請求書連携',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_ar_invoice_invoice_no` (`invoice_no`),
  KEY `idx_fin_ar_invoice_partner_id` (`partner_id`),
  KEY `idx_fin_ar_invoice_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='売掛請求書';

SET FOREIGN_KEY_CHECKS = 1;
