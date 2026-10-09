-- TABLE: fin_ap_bill
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_ap_bill` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `bill_no` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '仕入請求番号',
  `partner_id` int DEFAULT NULL COMMENT '仕入先',
  `partner_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '取引先名',
  `bill_date` date NOT NULL COMMENT '請求日',
  `due_date` date DEFAULT NULL COMMENT '支払期限',
  `subtotal` decimal(18,2) DEFAULT '0.00' COMMENT '税抜金額',
  `tax_amount` decimal(18,2) DEFAULT '0.00' COMMENT '消費税額',
  `total_amount` decimal(18,2) DEFAULT '0.00' COMMENT '合計金額',
  `paid_amount` decimal(18,2) DEFAULT '0.00' COMMENT '支払済金額',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'draft' COMMENT '状態（下書き/確定/支払済）',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_ap_bill_bill_no` (`bill_no`),
  KEY `idx_fin_ap_bill_partner_id` (`partner_id`),
  KEY `idx_fin_ap_bill_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='買掛請求';

SET FOREIGN_KEY_CHECKS = 1;
