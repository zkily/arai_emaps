-- TABLE: fin_ap_payment
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_ap_payment` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `payment_no` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '支払番号',
  `partner_id` int DEFAULT NULL COMMENT '取引先ID',
  `payment_date` date NOT NULL COMMENT '支払日',
  `amount` decimal(18,2) DEFAULT '0.00' COMMENT '金額',
  `method` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '支払方法（振込/手形）',
  `bank_account_id` int DEFAULT NULL COMMENT '出金口座',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'scheduled' COMMENT '状態（予定/支払済）',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_ap_payment_payment_no` (`payment_no`),
  KEY `idx_fin_ap_payment_partner_id` (`partner_id`),
  KEY `idx_fin_ap_payment_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='支払';

SET FOREIGN_KEY_CHECKS = 1;
