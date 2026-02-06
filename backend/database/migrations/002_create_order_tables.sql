-- ================================================================
-- 受注管理システム データベースマイグレーション
-- Order Management System Database Migration
-- Version: 002
-- Created: 2026-01-07
-- ================================================================

-- ================================================================
-- 1. 顧客マスタテーブル (Customer Master)
-- ================================================================
CREATE TABLE IF NOT EXISTS `customer` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
  `customer_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '顧客コード',
  `customer_name` VARCHAR(200) NOT NULL COMMENT '顧客名',
  `customer_name_kana` VARCHAR(200) DEFAULT NULL COMMENT '顧客名カナ',
  `postal_code` VARCHAR(10) DEFAULT NULL COMMENT '郵便番号',
  `address` VARCHAR(500) DEFAULT NULL COMMENT '住所',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '電話番号',
  `fax` VARCHAR(20) DEFAULT NULL COMMENT 'FAX番号',
  `email` VARCHAR(100) DEFAULT NULL COMMENT 'メールアドレス',
  `contact_person` VARCHAR(100) DEFAULT NULL COMMENT '担当者名',
  `contact_phone` VARCHAR(20) DEFAULT NULL COMMENT '担当者電話番号',
  `contact_email` VARCHAR(100) DEFAULT NULL COMMENT '担当者メール',
  `remarks` TEXT DEFAULT NULL COMMENT '備考',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '有効フラグ',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  INDEX `idx_customer_code` (`customer_code`),
  INDEX `idx_customer_name` (`customer_name`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='顧客マスタ';

-- ================================================================
-- 2. 納入先マスタテーブル (Destination Master)
-- ================================================================
CREATE TABLE IF NOT EXISTS `destination` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
  `destination_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '納入先コード',
  `destination_name` VARCHAR(200) NOT NULL COMMENT '納入先名',
  `destination_name_kana` VARCHAR(200) DEFAULT NULL COMMENT '納入先名カナ',
  `customer_code` VARCHAR(50) DEFAULT NULL COMMENT '顧客コード',
  `customer_name` VARCHAR(200) DEFAULT NULL COMMENT '顧客名',
  `postal_code` VARCHAR(10) DEFAULT NULL COMMENT '郵便番号',
  `address` VARCHAR(500) DEFAULT NULL COMMENT '住所',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '電話番号',
  `remarks` TEXT DEFAULT NULL COMMENT '備考',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '有効フラグ',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  INDEX `idx_destination_code` (`destination_code`),
  INDEX `idx_customer_code` (`customer_code`),
  INDEX `idx_destination_name` (`destination_name`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='納入先マスタ';

-- ================================================================
-- 3. 製品マスタテーブル (Product Master)
-- ================================================================
CREATE TABLE IF NOT EXISTS `product` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
  `product_code` VARCHAR(100) NOT NULL UNIQUE COMMENT '品番',
  `product_name` VARCHAR(300) NOT NULL COMMENT '品名',
  `product_name_kana` VARCHAR(300) DEFAULT NULL COMMENT '品名カナ',
  `category` VARCHAR(100) DEFAULT NULL COMMENT 'カテゴリ',
  `specification` TEXT DEFAULT NULL COMMENT '仕様',
  `unit` VARCHAR(20) DEFAULT '個' COMMENT '単位',
  `standard_price` DECIMAL(10, 2) DEFAULT NULL COMMENT '標準単価',
  `cost_price` DECIMAL(10, 2) DEFAULT NULL COMMENT '原価',
  `remarks` TEXT DEFAULT NULL COMMENT '備考',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '有効フラグ',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  INDEX `idx_product_code` (`product_code`),
  INDEX `idx_product_name` (`product_name`(100)),
  INDEX `idx_category` (`category`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='製品マスタ';

-- ================================================================
-- 4. 月別受注管理テーブル (Monthly Order Management)
-- ================================================================
CREATE TABLE IF NOT EXISTS `order_monthly` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
  `year` INT NOT NULL COMMENT '年',
  `month` INT NOT NULL COMMENT '月',
  `customer_code` VARCHAR(50) NOT NULL COMMENT '顧客コード',
  `customer_name` VARCHAR(200) DEFAULT NULL COMMENT '顧客名',
  `product_code` VARCHAR(100) NOT NULL COMMENT '品番',
  `product_name` VARCHAR(300) DEFAULT NULL COMMENT '品名',
  `destination_code` VARCHAR(50) DEFAULT NULL COMMENT '納入先コード',
  `destination_name` VARCHAR(200) DEFAULT NULL COMMENT '納入先名',
  `forecast_units` INT DEFAULT 0 COMMENT '内示本数',
  `confirmed_units` INT DEFAULT 0 COMMENT '確定本数',
  `forecast_diff` INT DEFAULT 0 COMMENT '内示差異',
  `plating_type` VARCHAR(50) DEFAULT NULL COMMENT 'メッキ区分（社内/外注）',
  `plating_count` INT DEFAULT 0 COMMENT 'メッキ数',
  `welding_type` VARCHAR(50) DEFAULT NULL COMMENT '溶接区分（社内/外注）',
  `welding_count` INT DEFAULT 0 COMMENT '溶接数',
  `unit_price` DECIMAL(10, 2) DEFAULT NULL COMMENT '単価',
  `total_amount` DECIMAL(15, 2) DEFAULT NULL COMMENT '合計金額',
  `remarks` TEXT DEFAULT NULL COMMENT '備考',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '有効フラグ',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `created_by` VARCHAR(100) DEFAULT NULL COMMENT '作成者',
  `updated_by` VARCHAR(100) DEFAULT NULL COMMENT '更新者',
  INDEX `idx_year_month` (`year`, `month`),
  INDEX `idx_customer_code` (`customer_code`),
  INDEX `idx_product_code` (`product_code`),
  INDEX `idx_destination_code` (`destination_code`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='月別受注管理';

-- ================================================================
-- 5. 日別受注管理テーブル (Daily Order Management)
-- ================================================================
CREATE TABLE IF NOT EXISTS `order_daily` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
  `monthly_order_id` INT DEFAULT NULL COMMENT '月別受注ID',
  `year` INT NOT NULL COMMENT '年',
  `month` INT NOT NULL COMMENT '月',
  `day` INT NOT NULL COMMENT '日',
  `order_date` DATE NOT NULL COMMENT '受注日',
  `customer_code` VARCHAR(50) NOT NULL COMMENT '顧客コード',
  `customer_name` VARCHAR(200) DEFAULT NULL COMMENT '顧客名',
  `product_code` VARCHAR(100) NOT NULL COMMENT '品番',
  `product_name` VARCHAR(300) DEFAULT NULL COMMENT '品名',
  `destination_code` VARCHAR(50) DEFAULT NULL COMMENT '納入先コード',
  `destination_name` VARCHAR(200) DEFAULT NULL COMMENT '納入先名',
  `confirmed_boxes` INT DEFAULT 0 COMMENT '確定箱数',
  `confirmed_units` INT DEFAULT 0 COMMENT '確定本数',
  `forecast_units` INT DEFAULT 0 COMMENT '内示本数',
  `shipped_boxes` INT DEFAULT 0 COMMENT '出荷箱数',
  `shipped_units` INT DEFAULT 0 COMMENT '出荷本数',
  `shipping_status` VARCHAR(20) DEFAULT '未出荷' COMMENT '出荷状態（出荷済/未出荷）',
  `confirmation_status` VARCHAR(20) DEFAULT '未確認' COMMENT '確認状態（確認済/未確認）',
  `is_shipped` BOOLEAN DEFAULT FALSE COMMENT '出荷済フラグ',
  `is_confirmed` BOOLEAN DEFAULT FALSE COMMENT '確認済フラグ',
  `unit_price` DECIMAL(10, 2) DEFAULT NULL COMMENT '単価',
  `total_amount` DECIMAL(15, 2) DEFAULT NULL COMMENT '合計金額',
  `remarks` TEXT DEFAULT NULL COMMENT '備考',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '有効フラグ',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `created_by` VARCHAR(100) DEFAULT NULL COMMENT '作成者',
  `updated_by` VARCHAR(100) DEFAULT NULL COMMENT '更新者',
  INDEX `idx_monthly_order_id` (`monthly_order_id`),
  INDEX `idx_year_month_day` (`year`, `month`, `day`),
  INDEX `idx_order_date` (`order_date`),
  INDEX `idx_customer_code` (`customer_code`),
  INDEX `idx_product_code` (`product_code`),
  INDEX `idx_destination_code` (`destination_code`),
  INDEX `idx_shipping_status` (`shipping_status`),
  INDEX `idx_confirmation_status` (`confirmation_status`),
  INDEX `idx_is_shipped` (`is_shipped`),
  INDEX `idx_is_confirmed` (`is_confirmed`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_created_at` (`created_at`),
  FOREIGN KEY (`monthly_order_id`) REFERENCES `order_monthly` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='日別受注管理';

-- ================================================================
-- 6. 受注ログテーブル (Order Log)
-- ================================================================
CREATE TABLE IF NOT EXISTS `order_log` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
  `order_type` VARCHAR(20) NOT NULL COMMENT '受注タイプ（monthly/daily）',
  `order_id` INT NOT NULL COMMENT '受注ID',
  `action` VARCHAR(50) NOT NULL COMMENT '操作（create/update/delete/sync）',
  `old_data` TEXT DEFAULT NULL COMMENT '変更前データ（JSON）',
  `new_data` TEXT DEFAULT NULL COMMENT '変更後データ（JSON）',
  `user_id` INT DEFAULT NULL COMMENT 'ユーザーID',
  `user_name` VARCHAR(100) DEFAULT NULL COMMENT 'ユーザー名',
  `ip_address` VARCHAR(50) DEFAULT NULL COMMENT 'IPアドレス',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  INDEX `idx_order_type` (`order_type`),
  INDEX `idx_order_id` (`order_id`),
  INDEX `idx_action` (`action`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='受注ログ';

-- ================================================================
-- 7. サンプルデータの挿入 (Sample Data)
-- ================================================================

-- 顧客サンプルデータ
INSERT IGNORE INTO `customer` (`customer_code`, `customer_name`, `customer_name_kana`, `phone`, `email`, `remarks`) VALUES
('C001', 'トヨタ自動車株式会社', 'トヨタジドウシャカブシキガイシャ', '03-1234-5678', 'contact@toyota.example.jp', 'メインカスタマー'),
('C002', '日産自動車株式会社', 'ニッサンジドウシャカブシキガイシャ', '03-2234-5678', 'contact@nissan.example.jp', ''),
('C003', '本田技研工業株式会社', 'ホンダギケンコウギョウカブシキガイシャ', '03-3234-5678', 'contact@honda.example.jp', '');

-- 納入先サンプルデータ
INSERT IGNORE INTO `destination` (`destination_code`, `destination_name`, `customer_code`, `customer_name`, `address`) VALUES
('D001', 'トヨタ本社工場', 'C001', 'トヨタ自動車株式会社', '愛知県豊田市トヨタ町1番地'),
('D002', 'トヨタ九州工場', 'C001', 'トヨタ自動車株式会社', '福岡県宮若市'),
('D003', '日産追浜工場', 'C002', '日産自動車株式会社', '神奈川県横須賀市'),
('D004', 'ホンダ鈴鹿工場', 'C003', '本田技研工業株式会社', '三重県鈴鹿市');

-- 製品サンプルデータ
INSERT IGNORE INTO `product` (`product_code`, `product_name`, `category`, `unit`, `standard_price`) VALUES
('P001', 'エンジンパーツA', 'エンジン部品', '個', 1500.00),
('P002', 'エンジンパーツB', 'エンジン部品', '個', 2000.00),
('P003', 'ブレーキパッドC', 'ブレーキ部品', 'セット', 3500.00),
('P004', 'サスペンションD', '足回り部品', '個', 5000.00),
('P005', 'ボディパネルE', 'ボディ部品', '枚', 8000.00);

-- ================================================================
-- 8. ビューの作成 (Create Views)
-- ================================================================

-- 月別受注サマリービュー
CREATE OR REPLACE VIEW `v_order_monthly_summary` AS
SELECT 
  `year`,
  `month`,
  COUNT(*) as `order_count`,
  SUM(`forecast_units`) as `total_forecast_units`,
  SUM(`confirmed_units`) as `total_confirmed_units`,
  SUM(`forecast_diff`) as `total_forecast_diff`,
  SUM(`total_amount`) as `total_amount`,
  COUNT(DISTINCT `customer_code`) as `customer_count`,
  COUNT(DISTINCT `product_code`) as `product_count`
FROM `order_monthly`
WHERE `is_active` = TRUE
GROUP BY `year`, `month`
ORDER BY `year` DESC, `month` DESC;

-- 日別受注サマリービュー
CREATE OR REPLACE VIEW `v_order_daily_summary` AS
SELECT 
  `year`,
  `month`,
  `day`,
  `order_date`,
  COUNT(*) as `order_count`,
  SUM(`confirmed_boxes`) as `total_confirmed_boxes`,
  SUM(`confirmed_units`) as `total_confirmed_units`,
  SUM(`forecast_units`) as `total_forecast_units`,
  SUM(`shipped_boxes`) as `total_shipped_boxes`,
  SUM(`shipped_units`) as `total_shipped_units`,
  SUM(CASE WHEN `is_shipped` = TRUE THEN 1 ELSE 0 END) as `shipped_count`,
  SUM(CASE WHEN `is_shipped` = FALSE THEN 1 ELSE 0 END) as `unshipped_count`,
  SUM(CASE WHEN `is_confirmed` = TRUE THEN 1 ELSE 0 END) as `confirmed_count`,
  SUM(CASE WHEN `is_confirmed` = FALSE THEN 1 ELSE 0 END) as `unconfirmed_count`,
  SUM(`total_amount`) as `total_amount`
FROM `order_daily`
WHERE `is_active` = TRUE
GROUP BY `year`, `month`, `day`, `order_date`
ORDER BY `order_date` DESC;

-- 顧客別受注統計ビュー
CREATE OR REPLACE VIEW `v_customer_order_stats` AS
SELECT 
  c.`customer_code`,
  c.`customer_name`,
  COUNT(DISTINCT om.`id`) as `monthly_order_count`,
  COUNT(DISTINCT od.`id`) as `daily_order_count`,
  SUM(om.`confirmed_units`) as `total_monthly_units`,
  SUM(od.`confirmed_units`) as `total_daily_units`,
  SUM(om.`total_amount`) as `total_monthly_amount`,
  SUM(od.`total_amount`) as `total_daily_amount`
FROM `customer` c
LEFT JOIN `order_monthly` om ON c.`customer_code` = om.`customer_code` AND om.`is_active` = TRUE
LEFT JOIN `order_daily` od ON c.`customer_code` = od.`customer_code` AND od.`is_active` = TRUE
WHERE c.`is_active` = TRUE
GROUP BY c.`customer_code`, c.`customer_name`;

-- ================================================================
-- マイグレーション完了
-- ================================================================
SELECT 'Order Management System Migration 002 completed successfully.' as message;

