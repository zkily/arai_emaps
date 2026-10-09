-- SEED: supplier
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `supplier` (`id`, `supplier_code`, `supplier_name`, `supplier_name_kana`, `supplier_type`, `category`, `tax_id`, `postal_code`, `address`, `phone`, `fax`, `email`, `website`, `bank_name`, `bank_branch`, `bank_account_type`, `bank_account_no`, `bank_account_name`, `payment_term`, `currency`, `credit_limit`, `rating`, `is_active`, `remarks`) VALUES
(1, 'SUP001', '株式会社サンプル商事', NULL, 'distributor', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'JPY', NULL, NULL, 1, NULL),
(2, 'SUP002', 'サンプルメーカー株式会社', NULL, 'manufacturer', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'JPY', NULL, NULL, 1, NULL);

SET FOREIGN_KEY_CHECKS = 1;
