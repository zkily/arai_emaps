-- SEED: fin_pay_item
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `fin_pay_item` (`id`, `code`, `name`, `item_type`, `is_taxable`, `account_code`, `is_active`, `created_by`, `updated_by`) VALUES
(1, 'BASE', '基本給', 'earning', 1, '710', 1, NULL, NULL),
(2, 'OVERTIME', '時間外手当', 'earning', 1, '710', 1, NULL, NULL),
(3, 'COMMUTE', '通勤手当', 'earning', 0, '730', 1, NULL, NULL),
(4, 'HEALTH', '健康保険', 'deduction', 0, '320', 1, NULL, NULL),
(5, 'PENSION', '厚生年金', 'deduction', 0, '320', 1, NULL, NULL),
(6, 'EMPLOY', '雇用保険', 'deduction', 0, '320', 1, NULL, NULL),
(7, 'INCOMETAX', '所得税', 'deduction', 0, '320', 1, NULL, NULL),
(8, 'RESIDENT', '住民税', 'deduction', 0, '320', 1, NULL, NULL);

SET FOREIGN_KEY_CHECKS = 1;
