-- SEED: fin_tax_code
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `fin_tax_code` (`id`, `code`, `name`, `rate`, `kind`, `is_active`, `created_by`, `updated_by`) VALUES
(1, 'TAX10', '課税仕入10%', 10.000, 'taxable', 1, NULL, NULL),
(2, 'TAX8', '軽減税率8%', 8.000, 'taxable', 1, NULL, NULL),
(3, 'OUT10', '課税売上10%', 10.000, 'taxable', 1, NULL, NULL),
(4, 'EXEMPT', '非課税', 0.000, 'exempt', 1, NULL, NULL),
(5, 'NONTAX', '不課税', 0.000, 'non_taxable', 1, NULL, NULL);

SET FOREIGN_KEY_CHECKS = 1;
