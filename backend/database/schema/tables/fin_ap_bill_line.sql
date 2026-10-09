-- TABLE: fin_ap_bill_line
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `fin_ap_bill_line` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `bill_id` bigint NOT NULL COMMENT '親レコードID',
  `line_no` int DEFAULT '1' COMMENT '行番号',
  `item_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品目名',
  `quantity` decimal(18,4) DEFAULT '0.0000' COMMENT '数量',
  `unit_price` decimal(18,4) DEFAULT '0.0000' COMMENT '単価',
  `tax_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '税区分コード',
  `amount` decimal(18,2) DEFAULT '0.00' COMMENT '金額',
  `account_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '値（費用/仕入科目）',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_fin_ap_bill_line_bill_id` (`bill_id`),
  CONSTRAINT `fk_fin_ap_bill_line_bill_id` FOREIGN KEY (`bill_id`) REFERENCES `fin_ap_bill` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='買掛請求明細';

SET FOREIGN_KEY_CHECKS = 1;
