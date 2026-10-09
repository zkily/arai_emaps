-- SEED: fin_company_settings
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `fin_company_settings` (`id`, `company_name`, `fiscal_start_month`, `tax_method`, `rounding`, `base_currency`, `created_by`, `updated_by`) VALUES
(1, 'Smart-EMAPs 株式会社', 4, 'invoice', 'round', 'JPY', NULL, NULL);

SET FOREIGN_KEY_CHECKS = 1;
