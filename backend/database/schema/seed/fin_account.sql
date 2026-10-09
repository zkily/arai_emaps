-- SEED: fin_account
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `fin_account` (`id`, `code`, `name`, `account_type`, `parent_code`, `default_tax_code`, `is_active`, `sort_order`, `created_by`, `updated_by`) VALUES
(1, '100', '現金', 'asset', NULL, NULL, 1, 0, NULL, NULL),
(2, '110', '普通預金', 'asset', NULL, NULL, 1, 1, NULL, NULL),
(3, '135', '売掛金', 'asset', NULL, NULL, 1, 2, NULL, NULL),
(4, '140', '棚卸資産', 'asset', NULL, NULL, 1, 3, NULL, NULL),
(5, '145', '仕掛品', 'asset', NULL, NULL, 1, 4, NULL, NULL),
(6, '146', '製品', 'asset', NULL, NULL, 1, 5, NULL, NULL),
(7, '170', '建物附属設備', 'asset', NULL, NULL, 1, 6, NULL, NULL),
(8, '175', '機械装置', 'asset', NULL, NULL, 1, 7, NULL, NULL),
(9, '180', '減価償却累計額', 'asset', NULL, NULL, 1, 8, NULL, NULL),
(10, '305', '買掛金', 'liability', NULL, NULL, 1, 9, NULL, NULL),
(11, '310', '未払金', 'liability', NULL, NULL, 1, 10, NULL, NULL),
(12, '315', '未払費用', 'liability', NULL, NULL, 1, 11, NULL, NULL),
(13, '320', '預り金', 'liability', NULL, NULL, 1, 12, NULL, NULL),
(14, '500', '資本金', 'equity', NULL, NULL, 1, 13, NULL, NULL),
(15, '600', '売上高', 'revenue', NULL, NULL, 1, 14, NULL, NULL),
(16, '700', '仕入高', 'expense', NULL, NULL, 1, 15, NULL, NULL),
(17, '705', '外注加工費', 'expense', NULL, NULL, 1, 16, NULL, NULL),
(18, '710', '給与手当', 'expense', NULL, NULL, 1, 17, NULL, NULL),
(19, '715', '法定福利費', 'expense', NULL, NULL, 1, 18, NULL, NULL),
(20, '720', '減価償却費', 'expense', NULL, NULL, 1, 19, NULL, NULL),
(21, '730', '旅費交通費', 'expense', NULL, NULL, 1, 20, NULL, NULL),
(22, '735', '通信費', 'expense', NULL, NULL, 1, 21, NULL, NULL),
(23, '740', '消耗品費', 'expense', NULL, NULL, 1, 22, NULL, NULL),
(24, '745', '会議費', 'expense', NULL, NULL, 1, 23, NULL, NULL),
(25, '750', '棚卸差額', 'expense', NULL, NULL, 1, 24, NULL, NULL);

SET FOREIGN_KEY_CHECKS = 1;
