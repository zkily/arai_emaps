-- SEED: customer
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `customer` (`id`, `customer_code`, `customer_name`, `customer_name_kana`, `postal_code`, `address`, `phone`, `fax`, `email`, `contact_person`, `contact_phone`, `contact_email`, `remarks`, `is_active`) VALUES
(1, 'C001', 'トヨタ自動車株式会社', 'トヨタジドウシャカブシキガイシャ', NULL, NULL, '03-1234-5678', NULL, 'contact@toyota.example.jp', NULL, NULL, NULL, 'メインカスタマー', 1),
(2, 'C002', '日産自動車株式会社', 'ニッサンジドウシャカブシキガイシャ', NULL, NULL, '03-2234-5678', NULL, 'contact@nissan.example.jp', NULL, NULL, NULL, '', 1),
(3, 'C003', '本田技研工業株式会社', 'ホンダギケンコウギョウカブシキガイシャ', NULL, NULL, '03-3234-5678', NULL, 'contact@honda.example.jp', NULL, NULL, NULL, '', 1);

SET FOREIGN_KEY_CHECKS = 1;
