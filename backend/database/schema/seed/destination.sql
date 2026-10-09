-- SEED: destination
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `destination` (`id`, `destination_code`, `destination_name`, `destination_name_kana`, `customer_code`, `customer_name`, `postal_code`, `address`, `phone`, `remarks`, `is_active`) VALUES
(1, 'D001', 'トヨタ本社工場', NULL, 'C001', 'トヨタ自動車株式会社', NULL, '愛知県豊田市トヨタ町1番地', NULL, NULL, 1),
(2, 'D002', 'トヨタ九州工場', NULL, 'C001', 'トヨタ自動車株式会社', NULL, '福岡県宮若市', NULL, NULL, 1),
(3, 'D003', '日産追浜工場', NULL, 'C002', '日産自動車株式会社', NULL, '神奈川県横須賀市', NULL, NULL, 1),
(4, 'D004', 'ホンダ鈴鹿工場', NULL, 'C003', '本田技研工業株式会社', NULL, '三重県鈴鹿市', NULL, NULL, 1);

SET FOREIGN_KEY_CHECKS = 1;
