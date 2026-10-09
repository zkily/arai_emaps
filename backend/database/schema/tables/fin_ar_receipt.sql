-- TABLE: fin_ar_receipt
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_ar_receipt` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `receipt_no` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '入金番号',
  `partner_id` int DEFAULT NULL COMMENT '取引先ID',
  `receipt_date` date NOT NULL COMMENT '入金日',
  `amount` decimal(18,2) DEFAULT '0.00' COMMENT '入金額',
  `method` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '入金方法（振込/手形/現金）',
  `bank_account_id` int DEFAULT NULL COMMENT '入金口座',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'unmatched' COMMENT '状態（未消込/消込済）',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_ar_receipt_receipt_no` (`receipt_no`),
  KEY `idx_fin_ar_receipt_partner_id` (`partner_id`),
  KEY `idx_fin_ar_receipt_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='入金';

SET FOREIGN_KEY_CHECKS = 1;
