-- SEED: product
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `product` (`id`, `product_code`, `product_name`, `product_name_kana`, `category`, `specification`, `unit`, `standard_price`, `cost_price`, `remarks`, `is_active`) VALUES
(1, 'P001', 'エンジンパーツA', NULL, 'エンジン部品', NULL, '個', 1500.00, NULL, NULL, 1),
(2, 'P002', 'エンジンパーツB', NULL, 'エンジン部品', NULL, '個', 2000.00, NULL, NULL, 1),
(3, 'P003', 'ブレーキパッドC', NULL, 'ブレーキ部品', NULL, 'セット', 3500.00, NULL, NULL, 1),
(4, 'P004', 'サスペンションD', NULL, '足回り部品', NULL, '個', 5000.00, NULL, NULL, 1),
(5, 'P005', 'ボディパネルE', NULL, 'ボディ部品', NULL, '枚', 8000.00, NULL, NULL, 1);

SET FOREIGN_KEY_CHECKS = 1;
