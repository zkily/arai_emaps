-- =============================================================================
-- Smart-EMAP 全量基线（本文件: 02_baseline_full_schema.sql；由旧 002～260 迁移按序合并）
-- 执行顺序: 先 ../init/01_init.sql，再本文件；或仓库根目录 py scripts/bootstrap_full_database.py
-- 注意: 已在旧环境执行过本基线的库，勿再整文件重复执行（会与触发器/过程等重复定义）。
-- Generated: 2026-05-14T04:41:44.660767+00:00
-- =============================================================================


-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 002_create_order_tables.sql (original prefix 002)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

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

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 003_create_erp_tables.sql (original prefix 003)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ERP モジュール テーブル作成
-- 在庫管理、購買管理、販売管理

-- ========== 倉庫マスタ ==========
CREATE TABLE IF NOT EXISTS warehouse (
    id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_code VARCHAR(50) NOT NULL UNIQUE,
    warehouse_name VARCHAR(200) NOT NULL,
    warehouse_type VARCHAR(30) DEFAULT 'product' COMMENT 'material,product,semi_finished,defective,transit',
    address VARCHAR(500),
    manager VARCHAR(100),
    phone VARCHAR(20),
    capacity INT,
    is_active BOOLEAN DEFAULT TRUE,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_warehouse_code (warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 在庫マスタ ==========
CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    warehouse_code VARCHAR(50) NOT NULL,
    warehouse_name VARCHAR(200),
    quantity INT DEFAULT 0,
    available_quantity INT DEFAULT 0,
    reserved_quantity INT DEFAULT 0,
    unit VARCHAR(20) DEFAULT '個',
    unit_cost DECIMAL(12,2) DEFAULT 0,
    total_cost DECIMAL(15,2) DEFAULT 0,
    location VARCHAR(100),
    batch_no VARCHAR(100),
    production_date DATE,
    expiry_date DATE,
    min_stock_level INT DEFAULT 0,
    max_stock_level INT DEFAULT 0,
    reorder_point INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_inventory_product (product_code),
    INDEX idx_inventory_warehouse (warehouse_code),
    UNIQUE INDEX idx_inventory_product_warehouse (product_code, warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 在庫トランザクション ==========
CREATE TABLE IF NOT EXISTS inventory_transaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_no VARCHAR(50) NOT NULL UNIQUE,
    inventory_id INT,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    warehouse_code VARCHAR(50) NOT NULL,
    warehouse_name VARCHAR(200),
    transaction_type VARCHAR(30) NOT NULL COMMENT 'inbound,outbound,transfer_in,transfer_out,adjustment',
    quantity INT NOT NULL,
    unit_cost DECIMAL(12,2) DEFAULT 0,
    total_cost DECIMAL(15,2) DEFAULT 0,
    balance_before INT DEFAULT 0,
    balance_after INT DEFAULT 0,
    reference_type VARCHAR(50),
    reference_no VARCHAR(100),
    reference_id INT,
    batch_no VARCHAR(100),
    remarks TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_inv_trans_no (transaction_no),
    INDEX idx_inv_trans_product (product_code),
    INDEX idx_inv_trans_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 在庫調整 ==========
CREATE TABLE IF NOT EXISTS inventory_adjustment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    adjustment_no VARCHAR(50) NOT NULL UNIQUE,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    warehouse_code VARCHAR(50) NOT NULL,
    warehouse_name VARCHAR(200),
    adjustment_type VARCHAR(30) NOT NULL COMMENT 'increase,decrease,stocktaking',
    original_quantity INT NOT NULL,
    adjustment_quantity INT NOT NULL,
    new_quantity INT NOT NULL,
    reason VARCHAR(500),
    status VARCHAR(20) DEFAULT 'draft',
    remarks TEXT,
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_inv_adj_no (adjustment_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 在庫アラート ==========
CREATE TABLE IF NOT EXISTS stock_alert (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    warehouse_code VARCHAR(50) NOT NULL,
    warehouse_name VARCHAR(200),
    alert_type VARCHAR(30) NOT NULL COMMENT 'low_stock,overstock,expiring,expired',
    current_quantity INT,
    threshold_quantity INT,
    status VARCHAR(20) DEFAULT 'active',
    remarks TEXT,
    handled_at TIMESTAMP NULL,
    handled_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_alert_product (product_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 仕入先マスタ ==========
CREATE TABLE IF NOT EXISTS supplier (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_code VARCHAR(50) NOT NULL UNIQUE,
    supplier_name VARCHAR(200) NOT NULL,
    supplier_name_kana VARCHAR(200),
    supplier_type VARCHAR(30) DEFAULT 'manufacturer' COMMENT 'manufacturer,distributor,service,other',
    category VARCHAR(100),
    tax_id VARCHAR(50),
    postal_code VARCHAR(10),
    address VARCHAR(500),
    phone VARCHAR(20),
    fax VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(200),
    bank_name VARCHAR(100),
    bank_branch VARCHAR(100),
    bank_account_type VARCHAR(20),
    bank_account_no VARCHAR(50),
    bank_account_name VARCHAR(100),
    payment_term VARCHAR(100),
    currency VARCHAR(10) DEFAULT 'JPY',
    credit_limit DECIMAL(15,2),
    rating VARCHAR(1),
    is_active BOOLEAN DEFAULT TRUE,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_supplier_code (supplier_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 仕入先連絡先 ==========
CREATE TABLE IF NOT EXISTS supplier_contact (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    position VARCHAR(100),
    phone VARCHAR(20),
    mobile VARCHAR(20),
    email VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 発注テーブル ==========
CREATE TABLE IF NOT EXISTS purchase_order (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(50) NOT NULL UNIQUE,
    supplier_code VARCHAR(50) NOT NULL,
    supplier_name VARCHAR(200),
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    warehouse_code VARCHAR(50),
    warehouse_name VARCHAR(200),
    status VARCHAR(30) DEFAULT 'draft' COMMENT 'draft,pending,approved,partial_received,completed,cancelled',
    currency VARCHAR(10) DEFAULT 'JPY',
    exchange_rate DECIMAL(10,4) DEFAULT 1,
    subtotal DECIMAL(15,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 10,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    discount_rate DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    paid_amount DECIMAL(15,2) DEFAULT 0,
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_term VARCHAR(100),
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    delivery_address VARCHAR(500),
    remarks TEXT,
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_po_no (order_no),
    INDEX idx_po_supplier (supplier_code),
    INDEX idx_po_date (order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 発注明細 ==========
CREATE TABLE IF NOT EXISTS purchase_order_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    line_no INT NOT NULL,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    specification VARCHAR(500),
    unit VARCHAR(20) DEFAULT '個',
    quantity INT NOT NULL,
    received_quantity INT DEFAULT 0,
    unit_price DECIMAL(12,2) NOT NULL,
    tax_rate DECIMAL(5,2) DEFAULT 10,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    amount DECIMAL(15,2) NOT NULL,
    expected_delivery_date DATE,
    remarks TEXT,
    FOREIGN KEY (order_id) REFERENCES purchase_order(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 受注テーブル ==========
CREATE TABLE IF NOT EXISTS sales_order (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(50) NOT NULL UNIQUE,
    customer_code VARCHAR(50) NOT NULL,
    customer_name VARCHAR(200),
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    delivery_address VARCHAR(500),
    status VARCHAR(30) DEFAULT 'draft' COMMENT 'draft,pending,approved,partial_delivered,completed,cancelled',
    currency VARCHAR(10) DEFAULT 'JPY',
    exchange_rate DECIMAL(10,4) DEFAULT 1,
    subtotal DECIMAL(15,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 10,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    discount_rate DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    received_amount DECIMAL(15,2) DEFAULT 0,
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_term VARCHAR(100),
    sales_person VARCHAR(100),
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    remarks TEXT,
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_so_no (order_no),
    INDEX idx_so_customer (customer_code),
    INDEX idx_so_date (order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 受注明細 ==========
CREATE TABLE IF NOT EXISTS sales_order_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    line_no INT NOT NULL,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    specification VARCHAR(500),
    unit VARCHAR(20) DEFAULT '個',
    quantity INT NOT NULL,
    delivered_quantity INT DEFAULT 0,
    unit_price DECIMAL(12,2) NOT NULL,
    tax_rate DECIMAL(5,2) DEFAULT 10,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    amount DECIMAL(15,2) NOT NULL,
    warehouse_code VARCHAR(50),
    expected_delivery_date DATE,
    remarks TEXT,
    FOREIGN KEY (order_id) REFERENCES sales_order(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 出荷テーブル ==========
CREATE TABLE IF NOT EXISTS sales_delivery (
    id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_no VARCHAR(50) NOT NULL UNIQUE,
    order_id INT,
    order_no VARCHAR(50),
    customer_code VARCHAR(50) NOT NULL,
    customer_name VARCHAR(200),
    warehouse_code VARCHAR(50) NOT NULL,
    warehouse_name VARCHAR(200),
    delivery_date DATE NOT NULL,
    delivery_address VARCHAR(500),
    status VARCHAR(20) DEFAULT 'draft' COMMENT 'draft,confirmed,shipped,completed',
    tracking_no VARCHAR(100),
    carrier VARCHAR(100),
    total_quantity INT DEFAULT 0,
    remarks TEXT,
    created_by VARCHAR(100),
    confirmed_by VARCHAR(100),
    confirmed_at TIMESTAMP NULL,
    shipped_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sd_no (delivery_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 出荷明細 ==========
CREATE TABLE IF NOT EXISTS sales_delivery_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_id INT NOT NULL,
    order_item_id INT,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    unit VARCHAR(20) DEFAULT '個',
    ordered_quantity INT DEFAULT 0,
    delivery_quantity INT NOT NULL,
    batch_no VARCHAR(100),
    remarks TEXT,
    FOREIGN KEY (delivery_id) REFERENCES sales_delivery(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== 初期データ投入 ==========

-- 倉庫マスタ
INSERT INTO warehouse (warehouse_code, warehouse_name, warehouse_type, is_active) VALUES
('WH001', '本社倉庫', 'product', TRUE),
('WH002', '原材料倉庫', 'material', TRUE),
('WH003', '出荷センター', 'product', TRUE)
ON DUPLICATE KEY UPDATE warehouse_name = VALUES(warehouse_name);

-- 仕入先マスタ（サンプル）
INSERT INTO supplier (supplier_code, supplier_name, supplier_type, is_active) VALUES
('SUP001', '株式会社サンプル商事', 'distributor', TRUE),
('SUP002', 'サンプルメーカー株式会社', 'manufacturer', TRUE)
ON DUPLICATE KEY UPDATE supplier_name = VALUES(supplier_name);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 004_create_system_tables.sql (original prefix 004)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ============================================================
-- システム管理テーブル作成 (MySQL)
-- 組織、ロール、権限、メニュー管理
-- ============================================================

-- ========== 組織テーブル ==========
CREATE TABLE IF NOT EXISTS organizations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '組織コード（一意）',
    name VARCHAR(200) NOT NULL COMMENT '組織名',
    type VARCHAR(20) NOT NULL COMMENT '種類（company:会社, site:拠点, department:部門, line:ライン）',
    parent_id INT NULL COMMENT '親組織ID',
    manager_name VARCHAR(100) NULL COMMENT '責任者名',
    location VARCHAR(200) NULL COMMENT '所在地',
    phone VARCHAR(50) NULL COMMENT '電話番号',
    email VARCHAR(100) NULL COMMENT 'メールアドレス',
    description TEXT NULL COMMENT '説明',
    sort_order INT DEFAULT 0 COMMENT '表示順序',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_organizations_parent (parent_id),
    INDEX idx_organizations_type (type),
    CONSTRAINT fk_organizations_parent FOREIGN KEY (parent_id) REFERENCES organizations(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='組織テーブル（会社、拠点、部門、ライン）';


-- ========== ロールテーブル ==========
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT 'ロール名',
    description TEXT NULL COMMENT '説明',
    is_system TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'システムロールフラグ（1:削除不可）',
    data_scope VARCHAR(20) NOT NULL DEFAULT 'department' COMMENT 'データ参照範囲（self/department/department_below/all/custom）',
    custom_departments JSON NULL COMMENT 'カスタム部門リスト（data_scope=customの場合）',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ロールテーブル';


-- ========== メニューテーブル ==========
CREATE TABLE IF NOT EXISTS menus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'メニューコード',
    name VARCHAR(100) NOT NULL COMMENT 'メニュー名',
    parent_id INT NULL COMMENT '親メニューID',
    path VARCHAR(200) NULL COMMENT 'ルートパス',
    icon VARCHAR(50) NULL COMMENT 'アイコン名',
    sort_order INT DEFAULT 0 COMMENT '表示順序',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_menus_parent (parent_id),
    CONSTRAINT fk_menus_parent FOREIGN KEY (parent_id) REFERENCES menus(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='メニューテーブル';


-- ========== ロール・メニュー権限関連テーブル ==========
CREATE TABLE IF NOT EXISTS role_menu_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL COMMENT 'ロールID',
    menu_id INT NOT NULL COMMENT 'メニューID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    UNIQUE KEY uk_role_menu (role_id, menu_id),
    INDEX idx_role_menu_permissions_role (role_id),
    INDEX idx_role_menu_permissions_menu (menu_id),
    CONSTRAINT fk_rmp_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_rmp_menu FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ロール・メニュー権限関連テーブル';


-- ========== ロール・操作権限テーブル ==========
CREATE TABLE IF NOT EXISTS role_operation_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL COMMENT 'ロールID',
    module VARCHAR(100) NOT NULL COMMENT 'モジュール名',
    can_create TINYINT(1) DEFAULT 0 COMMENT '新規作成権限',
    can_edit TINYINT(1) DEFAULT 0 COMMENT '編集権限',
    can_delete TINYINT(1) DEFAULT 0 COMMENT '削除権限',
    can_export TINYINT(1) DEFAULT 0 COMMENT '出力権限',
    can_approve TINYINT(1) DEFAULT 0 COMMENT '承認権限',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    UNIQUE KEY uk_role_module (role_id, module),
    INDEX idx_rop_role (role_id),
    CONSTRAINT fk_rop_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ロール・操作権限テーブル';


-- ========== ユーザー・ロール関連テーブル ==========
CREATE TABLE IF NOT EXISTS user_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT 'ユーザーID',
    role_id INT NOT NULL COMMENT 'ロールID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    UNIQUE KEY uk_user_role (user_id, role_id),
    INDEX idx_user_roles_user (user_id),
    INDEX idx_user_roles_role (role_id),
    CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザー・ロール関連テーブル';


-- ========== ユーザーテーブル拡張（カラムが無い場合のみ追加） ==========
DELIMITER //
DROP PROCEDURE IF EXISTS add_system_user_columns//
CREATE PROCEDURE add_system_user_columns()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'department_id') = 0 THEN
    ALTER TABLE users ADD COLUMN department_id INT NULL COMMENT '所属部門ID';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'two_factor_enabled') = 0 THEN
    ALTER TABLE users ADD COLUMN two_factor_enabled TINYINT(1) DEFAULT 0 COMMENT '二要素認証有効フラグ';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'last_login_at') = 0 THEN
    ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP NULL COMMENT '最終ログイン日時';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'status') = 0 THEN
    ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active' COMMENT 'ステータス（active/locked/inactive）';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'idx_users_department') = 0 THEN
    ALTER TABLE users ADD INDEX idx_users_department (department_id);
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'idx_users_status') = 0 THEN
    ALTER TABLE users ADD INDEX idx_users_status (status);
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND CONSTRAINT_NAME = 'fk_users_department') = 0 THEN
    ALTER TABLE users ADD CONSTRAINT fk_users_department FOREIGN KEY (department_id) REFERENCES organizations(id) ON DELETE SET NULL;
  END IF;
END//
DELIMITER ;
CALL add_system_user_columns();
DROP PROCEDURE add_system_user_columns;


-- ========== 初期データ投入 ==========

-- デフォルト組織
INSERT INTO organizations (code, name, type, parent_id, sort_order) VALUES
('COMP001', '株式会社Smart-EMAP', 'company', NULL, 1)
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'SITE001', '本社', 'site', id, 1 FROM organizations WHERE code = 'COMP001' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'SITE002', '大阪工場', 'site', id, 2 FROM organizations WHERE code = 'COMP001' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'DEPT001', '営業部', 'department', id, 1 FROM organizations WHERE code = 'SITE001' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'DEPT002', '管理部', 'department', id, 2 FROM organizations WHERE code = 'SITE001' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'DEPT003', '製造部', 'department', id, 1 FROM organizations WHERE code = 'SITE002' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'DEPT004', '品質管理部', 'department', id, 2 FROM organizations WHERE code = 'SITE002' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'LINE001', '第1ライン', 'line', id, 1 FROM organizations WHERE code = 'DEPT003' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO organizations (code, name, type, parent_id, sort_order)
SELECT 'LINE002', '第2ライン', 'line', id, 2 FROM organizations WHERE code = 'DEPT003' LIMIT 1
ON DUPLICATE KEY UPDATE name = VALUES(name);


-- デフォルトロール
INSERT INTO roles (name, description, is_system, data_scope) VALUES
('管理者', 'システム管理者（全権限）', 1, 'all'),
('一般ユーザー', '一般ユーザー（読み書き権限）', 1, 'department'),
('閲覧者', '閲覧のみ', 0, 'department')
ON DUPLICATE KEY UPDATE description = VALUES(description);


-- デフォルトメニュー（INSERT IGNORE で重複時はスキップ）
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order) VALUES
('SYSTEM', 'システム管理', NULL, '/system', 'Setting', 1),
('ERP', 'ERP', NULL, '/erp', 'Management', 2),
('APS', 'APS', NULL, '/aps', 'DataAnalysis', 3),
('MES', 'MES', NULL, '/mes', 'Monitor', 4);

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'SYSTEM_USER', 'ユーザー管理', m.id, '/system/users', 'User', 1 FROM menus m WHERE m.code = 'SYSTEM' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'SYSTEM_ORG', '組織管理', m.id, '/system/organization', 'OfficeBuilding', 2 FROM menus m WHERE m.code = 'SYSTEM' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'SYSTEM_ROLE', '権限管理', m.id, '/system/roles', 'Lock', 3 FROM menus m WHERE m.code = 'SYSTEM' LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_SALES', '販売管理', m.id, '/erp/sales', 'Sell', 1 FROM menus m WHERE m.code = 'ERP' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_PURCHASE', '購買管理', m.id, '/erp/purchase', 'ShoppingCart', 2 FROM menus m WHERE m.code = 'ERP' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_INVENTORY', '在庫管理', m.id, '/erp/inventory', 'Box', 3 FROM menus m WHERE m.code = 'ERP' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'ERP_COSTING', '原価・会計', m.id, '/erp/costing', 'Coin', 4 FROM menus m WHERE m.code = 'ERP' LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_PLANNING', '生産計画', m.id, '/aps/planning', 'Calendar', 1 FROM menus m WHERE m.code = 'APS' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_SCHEDULING', 'スケジューリング', m.id, '/aps/scheduling', 'Timer', 2 FROM menus m WHERE m.code = 'APS' LIMIT 1;

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_EXECUTION', '製造実行', m.id, '/mes/execution', 'Operation', 1 FROM menus m WHERE m.code = 'MES' LIMIT 1;
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_QUALITY', '品質管理', m.id, '/mes/quality', 'DocumentChecked', 2 FROM menus m WHERE m.code = 'MES' LIMIT 1;


-- 管理者ロールに全メニュー権限を付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id FROM menus;


-- 管理者ロールに全操作権限を付与
INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '販売管理', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '購買管理', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '在庫管理', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '原価・会計', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '生産計画', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '製造実行', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), '品質管理', 1, 1, 1, 1, 1
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=1, can_export=1, can_approve=1;


-- 一般ユーザーロールにERP/APS/MESメニュー権限を付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), id FROM menus
WHERE code LIKE 'ERP%' OR code LIKE 'APS%' OR code LIKE 'MES%';


-- 一般ユーザーロールに操作権限を付与（削除権限なし）
INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '販売管理', 1, 1, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=0, can_export=1, can_approve=0;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '購買管理', 1, 1, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=0, can_export=1, can_approve=0;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '在庫管理', 1, 1, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=0, can_export=1, can_approve=0;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '原価・会計', 0, 0, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=0, can_edit=0, can_delete=0, can_export=1, can_approve=0;

INSERT INTO role_operation_permissions (role_id, module, can_create, can_edit, can_delete, can_export, can_approve)
SELECT (SELECT id FROM roles WHERE name = '一般ユーザー' LIMIT 1), '生産計画', 1, 1, 0, 1, 0
ON DUPLICATE KEY UPDATE can_create=1, can_edit=1, can_delete=0, can_export=1, can_approve=0;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 005_create_settings_tables.sql (original prefix 005)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ============================================================
-- システム設定テーブル作成 (MySQL)
-- システムログ、採番ルール、ワークフロー、通知、データ管理
-- ============================================================

-- ========== システムログ関連 ==========

-- 操作ログテーブル
CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
    user_id INT NULL COMMENT 'ユーザーID',
    username VARCHAR(100) NULL COMMENT 'ユーザー名',
    action VARCHAR(50) NOT NULL COMMENT '操作（login/logout/create/update/delete）',
    module VARCHAR(100) NULL COMMENT 'モジュール名',
    target VARCHAR(500) NULL COMMENT '対象（例: 受注番号: SO-202602-0156）',
    target_id INT NULL COMMENT '対象レコードID',
    ip_address VARCHAR(45) NULL COMMENT 'IPアドレス',
    user_agent TEXT NULL COMMENT 'ユーザーエージェント',
    details JSON NULL COMMENT '詳細情報（変更前後の値など）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_operation_logs_timestamp (timestamp),
    INDEX idx_operation_logs_user (user_id),
    INDEX idx_operation_logs_action (action),
    INDEX idx_operation_logs_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作ログテーブル';


-- エラーログテーブル
CREATE TABLE IF NOT EXISTS error_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
    level VARCHAR(20) NOT NULL COMMENT 'レベル（ERROR/WARN/INFO）',
    source VARCHAR(200) NULL COMMENT 'ソース（サービス名・ファイル名）',
    message TEXT NOT NULL COMMENT 'エラーメッセージ',
    stack_trace TEXT NULL COMMENT 'スタックトレース',
    user_id INT NULL COMMENT 'ユーザーID',
    request_id VARCHAR(100) NULL COMMENT 'リクエストID',
    extra_data JSON NULL COMMENT '追加データ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_error_logs_timestamp (timestamp),
    INDEX idx_error_logs_level (level),
    INDEX idx_error_logs_source (source(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='エラーログテーブル';


-- API連携ログテーブル
CREATE TABLE IF NOT EXISTS api_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
    method VARCHAR(10) NOT NULL COMMENT 'HTTPメソッド（GET/POST/PUT/DELETE）',
    endpoint VARCHAR(500) NOT NULL COMMENT 'エンドポイント',
    status_code INT NOT NULL COMMENT 'HTTPステータスコード',
    duration INT NULL COMMENT '応答時間（ミリ秒）',
    client VARCHAR(100) NULL COMMENT 'クライアント（Web Frontend/Mobile App等）',
    user_id INT NULL COMMENT 'ユーザーID',
    ip_address VARCHAR(45) NULL COMMENT 'IPアドレス',
    request_body TEXT NULL COMMENT 'リクエストボディ',
    response_body TEXT NULL COMMENT 'レスポンスボディ（エラー時のみ）',
    error_message TEXT NULL COMMENT 'エラーメッセージ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_api_logs_timestamp (timestamp),
    INDEX idx_api_logs_endpoint (endpoint(200)),
    INDEX idx_api_logs_status (status_code),
    INDEX idx_api_logs_method (method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API連携ログテーブル';


-- ========== 採番ルール ==========

CREATE TABLE IF NOT EXISTS numbering_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'ルールコード（例: SALES_ORDER）',
    name VARCHAR(100) NOT NULL COMMENT 'ルール名（例: 受注番号）',
    prefix VARCHAR(20) NOT NULL COMMENT 'プレフィックス（例: SO）',
    format VARCHAR(100) NOT NULL COMMENT 'フォーマット（例: {PREFIX}-{YYYY}{MM}-{SEQ:4}）',
    start_number INT NOT NULL DEFAULT 1 COMMENT '連番開始値',
    increment INT NOT NULL DEFAULT 1 COMMENT '連番増分',
    current_number INT NOT NULL DEFAULT 0 COMMENT '現在の連番',
    reset_type VARCHAR(20) NOT NULL DEFAULT 'monthly' COMMENT 'リセットタイミング（never/daily/monthly/yearly）',
    last_reset_date DATE NULL COMMENT '最終リセット日',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    description TEXT NULL COMMENT '説明',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_numbering_rules_code (code),
    INDEX idx_numbering_rules_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='採番ルールテーブル';


-- ========== ワークフロー関連 ==========

-- 承認ルートテーブル
CREATE TABLE IF NOT EXISTS approval_routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT 'ルート名',
    type VARCHAR(20) NOT NULL COMMENT '種類（amount:金額, department:部門, custom:カスタム）',
    condition_type VARCHAR(50) NULL COMMENT '条件タイプ',
    condition_value VARCHAR(200) NULL COMMENT '条件値（例: 10万円未満, 営業部）',
    condition_min DECIMAL(15,2) NULL COMMENT '金額条件（最小）',
    condition_max DECIMAL(15,2) NULL COMMENT '金額条件（最大）',
    condition_department_id INT NULL COMMENT '部門条件',
    priority INT DEFAULT 0 COMMENT '優先度（同条件時の判定順序）',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_approval_routes_type (type),
    INDEX idx_approval_routes_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='承認ルートテーブル';


-- 承認ルートステップテーブル
CREATE TABLE IF NOT EXISTS approval_route_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL COMMENT '承認ルートID',
    step_order INT NOT NULL COMMENT 'ステップ順序（1から開始）',
    step_name VARCHAR(100) NOT NULL COMMENT 'ステップ名（例: 課長）',
    approver_type VARCHAR(20) NOT NULL COMMENT '承認者タイプ（role:ロール, user:特定ユーザー, position:役職）',
    approver_id INT NULL COMMENT '承認者ID（ユーザーID or ロールID）',
    approver_position VARCHAR(50) NULL COMMENT '役職名',
    is_optional TINYINT(1) DEFAULT 0 COMMENT 'スキップ可能フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_route_steps_route (route_id),
    INDEX idx_route_steps_order (route_id, step_order),
    CONSTRAINT fk_route_steps_route FOREIGN KEY (route_id) REFERENCES approval_routes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='承認ルートステップテーブル';


-- 代理承認テーブル
CREATE TABLE IF NOT EXISTS delegations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    delegator_id INT NOT NULL COMMENT '委任者ユーザーID',
    delegate_id INT NOT NULL COMMENT '代理者ユーザーID',
    start_date DATE NOT NULL COMMENT '開始日',
    end_date DATE NOT NULL COMMENT '終了日',
    scope VARCHAR(50) NOT NULL DEFAULT 'all' COMMENT '範囲（all:全承認, specific:特定）',
    scope_details JSON NULL COMMENT '範囲詳細（特定の場合）',
    reason VARCHAR(500) NULL COMMENT '理由',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'ステータス（active/expired/cancelled）',
    created_by INT NULL COMMENT '作成者',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_delegations_delegator (delegator_id),
    INDEX idx_delegations_delegate (delegate_id),
    INDEX idx_delegations_dates (start_date, end_date),
    INDEX idx_delegations_status (status),
    CONSTRAINT fk_delegations_delegator FOREIGN KEY (delegator_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_delegations_delegate FOREIGN KEY (delegate_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代理承認テーブル';


-- ワークフロー定義テーブル
CREATE TABLE IF NOT EXISTS workflow_definitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'ワークフローコード（例: WF_PO）',
    name VARCHAR(100) NOT NULL COMMENT 'ワークフロー名',
    document_type VARCHAR(50) NOT NULL COMMENT '対象伝票タイプ',
    approval_route_id INT NULL COMMENT 'デフォルト承認ルートID',
    timeout_days INT DEFAULT 3 COMMENT '承認期限（日数）',
    escalation_enabled TINYINT(1) DEFAULT 0 COMMENT 'エスカレーション有効',
    escalation_days INT NULL COMMENT 'エスカレーションまでの日数',
    escalation_target VARCHAR(100) NULL COMMENT 'エスカレーション先',
    auto_approve_enabled TINYINT(1) DEFAULT 0 COMMENT '自動承認有効',
    auto_approve_condition JSON NULL COMMENT '自動承認条件',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_workflow_defs_code (code),
    INDEX idx_workflow_defs_doctype (document_type),
    CONSTRAINT fk_workflow_defs_route FOREIGN KEY (approval_route_id) REFERENCES approval_routes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ワークフロー定義テーブル';


-- ========== 通知センター ==========

-- 通知設定テーブル
CREATE TABLE IF NOT EXISTS notification_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_code VARCHAR(50) NOT NULL UNIQUE COMMENT 'イベントコード',
    event_name VARCHAR(100) NOT NULL COMMENT 'イベント名',
    description VARCHAR(500) NULL COMMENT '説明',
    in_app_enabled TINYINT(1) DEFAULT 1 COMMENT 'アプリ内通知有効',
    email_enabled TINYINT(1) DEFAULT 0 COMMENT 'メール通知有効',
    slack_enabled TINYINT(1) DEFAULT 0 COMMENT 'Slack通知有効',
    line_enabled TINYINT(1) DEFAULT 0 COMMENT 'LINE通知有効',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_notification_settings_event (event_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知設定テーブル';


-- メールテンプレートテーブル
CREATE TABLE IF NOT EXISTS email_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'テンプレートコード',
    name VARCHAR(100) NOT NULL COMMENT 'テンプレート名',
    subject VARCHAR(200) NOT NULL COMMENT '件名（変数可）',
    body TEXT NOT NULL COMMENT '本文（HTML可、変数可）',
    event_code VARCHAR(50) NULL COMMENT '関連イベントコード',
    language VARCHAR(10) DEFAULT 'ja' COMMENT '言語',
    variables JSON NULL COMMENT '利用可能な変数一覧',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_email_templates_code (code),
    INDEX idx_email_templates_event (event_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='メールテンプレートテーブル';


-- 外部連携設定テーブル
CREATE TABLE IF NOT EXISTS integration_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_type VARCHAR(50) NOT NULL UNIQUE COMMENT 'サービスタイプ（slack/line/teams等）',
    config JSON NOT NULL COMMENT '設定情報（webhook_url, token等）',
    is_enabled TINYINT(1) DEFAULT 0 COMMENT '有効フラグ',
    last_test_at DATETIME NULL COMMENT '最終テスト日時',
    last_test_result VARCHAR(50) NULL COMMENT '最終テスト結果',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外部連携設定テーブル';


-- ========== データ管理 ==========

-- インポート/エクスポート履歴テーブル
CREATE TABLE IF NOT EXISTS import_export_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(20) NOT NULL COMMENT '種類（import/export）',
    master_type VARCHAR(50) NOT NULL COMMENT 'マスター種類',
    filename VARCHAR(255) NOT NULL COMMENT 'ファイル名',
    file_path VARCHAR(500) NULL COMMENT 'ファイルパス',
    format VARCHAR(20) NULL COMMENT 'フォーマット（csv/xlsx）',
    encoding VARCHAR(20) NULL COMMENT '文字コード',
    total_records INT DEFAULT 0 COMMENT '総件数',
    success_records INT DEFAULT 0 COMMENT '成功件数',
    error_records INT DEFAULT 0 COMMENT 'エラー件数',
    status VARCHAR(20) NOT NULL DEFAULT 'processing' COMMENT 'ステータス（processing/success/partial_error/failed）',
    error_details JSON NULL COMMENT 'エラー詳細',
    options JSON NULL COMMENT 'オプション（update_existing等）',
    user_id INT NULL COMMENT '実行ユーザーID',
    started_at DATETIME NULL COMMENT '開始日時',
    completed_at DATETIME NULL COMMENT '完了日時',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_import_export_type (type),
    INDEX idx_import_export_master (master_type),
    INDEX idx_import_export_status (status),
    INDEX idx_import_export_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='インポート/エクスポート履歴テーブル';


-- バックアップ設定テーブル
CREATE TABLE IF NOT EXISTS backup_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    auto_backup_enabled TINYINT(1) DEFAULT 0 COMMENT '自動バックアップ有効',
    schedule VARCHAR(20) NOT NULL DEFAULT 'daily' COMMENT 'スケジュール（daily/weekly/monthly）',
    schedule_time TIME DEFAULT '02:00:00' COMMENT '実行時刻',
    storage_path VARCHAR(500) NOT NULL DEFAULT '/backup/' COMMENT '保存先パス',
    retention_count INT DEFAULT 7 COMMENT '保持世代数',
    include_files TINYINT(1) DEFAULT 0 COMMENT 'ファイルも含める',
    compression_enabled TINYINT(1) DEFAULT 1 COMMENT '圧縮有効',
    encryption_enabled TINYINT(1) DEFAULT 0 COMMENT '暗号化有効',
    notify_on_complete TINYINT(1) DEFAULT 0 COMMENT '完了時通知',
    notify_on_error TINYINT(1) DEFAULT 1 COMMENT 'エラー時通知',
    updated_by INT NULL COMMENT '更新者',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='バックアップ設定テーブル';


-- バックアップ履歴テーブル
CREATE TABLE IF NOT EXISTS backup_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL COMMENT 'ファイル名',
    file_path VARCHAR(500) NOT NULL COMMENT 'ファイルパス',
    file_size BIGINT NULL COMMENT 'ファイルサイズ（バイト）',
    backup_type VARCHAR(20) NOT NULL DEFAULT 'auto' COMMENT 'タイプ（auto/manual）',
    status VARCHAR(20) NOT NULL DEFAULT 'completed' COMMENT 'ステータス（completed/failed）',
    error_message TEXT NULL COMMENT 'エラーメッセージ',
    started_at DATETIME NULL COMMENT '開始日時',
    completed_at DATETIME NULL COMMENT '完了日時',
    created_by INT NULL COMMENT '作成者（手動の場合）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_backup_history_type (backup_type),
    INDEX idx_backup_history_status (status),
    INDEX idx_backup_history_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='バックアップ履歴テーブル';


-- ========== 初期データ投入 ==========

-- デフォルト採番ルール
INSERT INTO numbering_rules (code, name, prefix, format, start_number, increment, current_number, reset_type) VALUES
('SALES_ORDER', '受注番号', 'SO', '{PREFIX}-{YYYY}{MM}-{SEQ:4}', 1, 1, 0, 'monthly'),
('QUOTATION', '見積番号', 'QT', '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', 1, 1, 0, 'daily'),
('PURCHASE_ORDER', '発注番号', 'PO', '{PREFIX}-{YYYY}-{SEQ:5}', 1, 1, 0, 'yearly'),
('INVOICE', '請求書番号', 'INV', '{PREFIX}{YYYY}{MM}-{SEQ:4}', 1, 1, 0, 'monthly'),
('SHIPMENT', '出荷番号', 'SHP', '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', 1, 1, 0, 'daily')
ON DUPLICATE KEY UPDATE name = VALUES(name);


-- デフォルト承認ルート
INSERT INTO approval_routes (name, type, condition_value, condition_min, condition_max, priority) VALUES
('通常購買承認', 'amount', '10万円未満', NULL, 100000, 1),
('高額購買承認', 'amount', '10万円以上100万円未満', 100000, 1000000, 2),
('大規模購買承認', 'amount', '100万円以上', 1000000, NULL, 3)
ON DUPLICATE KEY UPDATE name = VALUES(name);


-- 承認ルートステップ（通常購買承認）
INSERT INTO approval_route_steps (route_id, step_order, step_name, approver_type, approver_position)
SELECT id, 1, '申請者', 'position', '申請者' FROM approval_routes WHERE name = '通常購買承認' LIMIT 1
ON DUPLICATE KEY UPDATE step_name = VALUES(step_name);
INSERT INTO approval_route_steps (route_id, step_order, step_name, approver_type, approver_position)
SELECT id, 2, '課長', 'position', '課長' FROM approval_routes WHERE name = '通常購買承認' LIMIT 1
ON DUPLICATE KEY UPDATE step_name = VALUES(step_name);
INSERT INTO approval_route_steps (route_id, step_order, step_name, approver_type, approver_position)
SELECT id, 3, '部長', 'position', '部長' FROM approval_routes WHERE name = '通常購買承認' LIMIT 1
ON DUPLICATE KEY UPDATE step_name = VALUES(step_name);


-- デフォルト通知設定
INSERT INTO notification_settings (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled) VALUES
('APPROVAL_REQUEST', '承認依頼', '新しい承認依頼が届いた時', 1, 1, 1, 0),
('APPROVAL_COMPLETE', '承認完了', '承認が完了した時', 1, 1, 0, 0),
('APPROVAL_REJECT', '承認却下', '承認が却下された時', 1, 1, 1, 0),
('DELIVERY_ALERT', '納期アラート', '納期が近づいている時', 1, 1, 1, 1),
('STOCK_ALERT', '在庫アラート', '在庫が基準値を下回った時', 1, 1, 1, 0),
('SYSTEM_ERROR', 'システムエラー', 'システムエラーが発生した時', 1, 1, 1, 0)
ON DUPLICATE KEY UPDATE event_name = VALUES(event_name);


-- デフォルトメールテンプレート
INSERT INTO email_templates (code, name, subject, body, event_code, language) VALUES
('APPROVAL_REQUEST', '承認依頼', '【要承認】{document_type} #{document_no}', '<p>{approver_name}様</p><p>以下の承認依頼が届いています。</p><p>伝票種類: {document_type}<br>伝票番号: {document_no}<br>申請者: {requester_name}<br>金額: {amount}</p><p>システムにログインして承認処理を行ってください。</p>', 'APPROVAL_REQUEST', 'ja'),
('APPROVAL_COMPLETE', '承認完了', '【承認完了】{document_type} #{document_no}', '<p>{requester_name}様</p><p>以下の申請が承認されました。</p><p>伝票種類: {document_type}<br>伝票番号: {document_no}<br>承認者: {approver_name}</p>', 'APPROVAL_COMPLETE', 'ja'),
('PASSWORD_RESET', 'パスワードリセット', '【Smart-EMAP】パスワードリセット', '<p>{user_name}様</p><p>パスワードがリセットされました。</p><p>新しいパスワードでログインしてください。</p>', NULL, 'ja'),
('WELCOME', 'ようこそ', '【Smart-EMAP】アカウント作成完了', '<p>{user_name}様</p><p>Smart-EMAPへようこそ！</p><p>アカウントが作成されました。以下の情報でログインしてください。</p><p>ユーザー名: {username}<br>初期パスワード: {initial_password}</p>', NULL, 'ja')
ON DUPLICATE KEY UPDATE name = VALUES(name);


-- デフォルトバックアップ設定
INSERT INTO backup_settings (id, auto_backup_enabled, schedule, schedule_time, storage_path, retention_count) VALUES
(1, 1, 'daily', '02:00:00', '/backup/', 7)
ON DUPLICATE KEY UPDATE auto_backup_enabled = VALUES(auto_backup_enabled);


-- デフォルトワークフロー定義
INSERT INTO workflow_definitions (code, name, document_type, timeout_days, escalation_enabled)
SELECT 'WF_PO', '購買発注承認', '発注書', 3, 1
WHERE NOT EXISTS (SELECT 1 FROM workflow_definitions WHERE code = 'WF_PO');

INSERT INTO workflow_definitions (code, name, document_type, timeout_days, escalation_enabled)
SELECT 'WF_SO', '受注承認', '受注書', 2, 1
WHERE NOT EXISTS (SELECT 1 FROM workflow_definitions WHERE code = 'WF_SO');

INSERT INTO workflow_definitions (code, name, document_type, timeout_days, escalation_enabled)
SELECT 'WF_QT', '見積承認', '見積書', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM workflow_definitions WHERE code = 'WF_QT');

INSERT INTO workflow_definitions (code, name, document_type, timeout_days, escalation_enabled)
SELECT 'WF_INV', '請求書承認', '請求書', 5, 1
WHERE NOT EXISTS (SELECT 1 FROM workflow_definitions WHERE code = 'WF_INV');

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 007_create_products.sql (original prefix 007)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for products
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '製品ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD（ユニークな製品コード）',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品名称',
  `product_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品種別（例：量産品 / 試作品）',
  `location_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '製品倉庫' COMMENT '保管場所CD',
  `start_use_date` date NULL DEFAULT NULL COMMENT '使用開始日',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'カテゴリ（例：センサー、ケースなど）',
  `department_id` int NULL DEFAULT NULL COMMENT '所属部門ID（外部キー）',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '納入先CD（外部キー）',
  `process_count` int NULL DEFAULT 1 COMMENT '工程数（標準の製造工程数）',
  `lead_time` int NULL DEFAULT NULL COMMENT 'リードタイム（日数）',
  `lot_size` int NULL DEFAULT 1 COMMENT 'ロットサイズ（まとめて作る単位）',
  `is_multistage` tinyint(1) NULL DEFAULT 1 COMMENT '多段階工程フラグ（TRUE=多段階）',
  `priority` int NULL DEFAULT 2 COMMENT '製品の優先度（1=高, 2=中, 3=低）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT 'ステータス（active / inactive）',
  `part_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '部品番号（部品連携時の識別子）',
  `vehicle_model` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '対応車種',
  `box_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '梱包タイプ（例：段ボール、プラ箱）',
  `unit_per_box` int NULL DEFAULT NULL COMMENT '1箱あたりの入数',
  `dimensions` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'サイズ（例：100x200x300）',
  `weight` decimal(10, 2) NULL DEFAULT NULL COMMENT '重量（kg 単位）',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '使用材料CD（外部キー）',
  `cut_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長さ（mm）',
  `chamfer_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取り長さ（mm）',
  `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長さ（mm）',
  `take_count` int NULL DEFAULT NULL COMMENT '取り数（1材料あたりの取り個数）',
  `scrap_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '端材長さ（mm）',
  `bom_id` int NULL DEFAULT NULL COMMENT 'BOM ID（構成マスタ参照）',
  `route_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '工程ルートID（外部キー）',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '備考欄',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `safety_days` int NULL DEFAULT NULL COMMENT '安全在庫日数',
  `unit_price` decimal(10, 2) NULL DEFAULT NULL COMMENT '販売単価',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '別名',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_location_cd`(`location_cd` ASC) USING BTREE,
  INDEX `idx_start_use_date`(`start_use_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '製品マスタ（拡張版）' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 008_create_material_master.sql (original prefix 008)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for materials
-- ----------------------------
DROP TABLE IF EXISTS `material_master`;
DROP TABLE IF EXISTS `materials`;
CREATE TABLE `materials` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '材料ID',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '材料CD',
  `material_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '材料名',
  `material_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '材料種類',
  `standard_spec` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '規格',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '単位（kg / 本 / m など）',
  `diameter` decimal(10, 2) NULL DEFAULT NULL COMMENT '直径（mm）',
  `thickness` decimal(10, 2) NULL DEFAULT NULL COMMENT '厚さ（mm）',
  `length` decimal(10, 2) NULL DEFAULT NULL COMMENT '長さ（mm）',
  `supply_classification` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '支給区分（社内 / 支給）',
  `pieces_per_bundle` int NULL DEFAULT NULL COMMENT '束本数',
  `usegae` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用途',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '仕入先CD（外部キー）',
  `unit_price` decimal(10, 2) NULL DEFAULT NULL COMMENT '単重単価（円/kg 等）',
  `long_weight` decimal(10, 2) NULL DEFAULT NULL COMMENT '長尺単重（kg/本）',
  `single_price` decimal(10, 2) NULL DEFAULT NULL COMMENT '一本単価（円）',
  `safety_stock` int NULL DEFAULT 0 COMMENT '安全在庫（単位数）',
  `lead_time` int NULL DEFAULT NULL COMMENT 'リードタイム（日）',
  `storage_location` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '保管場所',
  `status` tinyint NULL DEFAULT 1 COMMENT '状態（1=有効, 0=無効）',
  `tolerance_range` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '公差範囲',
  `tolerance_1` decimal(10, 3) NULL DEFAULT NULL COMMENT '公差１',
  `tolerance_2` decimal(10, 3) NULL DEFAULT NULL COMMENT '公差２',
  `range_value` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '範囲',
  `min_value` decimal(10, 2) NULL DEFAULT NULL COMMENT '最小値',
  `max_value` decimal(10, 2) NULL DEFAULT NULL COMMENT '最大値',
  `actual_value_1` decimal(10, 3) NULL DEFAULT NULL COMMENT '実力値１',
  `actual_value_2` decimal(10, 3) NULL DEFAULT NULL COMMENT '実力値２',
  `actual_value_3` decimal(10, 3) NULL DEFAULT NULL COMMENT '実力値３',
  `representative_model` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '代表品種',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`, `material_cd`) USING BTREE,
  UNIQUE INDEX `material_cd`(`material_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '材料マスタ' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 009_create_suppliers.sql (original prefix 009)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for suppliers (マスタ用)
-- ----------------------------
DROP TABLE IF EXISTS `suppliers`;
CREATE TABLE `suppliers` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `supplier_cd` varchar(50) NOT NULL COMMENT '仕入先CD',
  `supplier_name` varchar(100) NOT NULL COMMENT '仕入先名',
  `supplier_kana` varchar(100) DEFAULT NULL COMMENT '仕入先カナ',
  `contact_person` varchar(100) DEFAULT NULL COMMENT '担当者',
  `phone` varchar(20) DEFAULT NULL COMMENT '電話番号',
  `fax` varchar(20) DEFAULT NULL COMMENT 'FAX番号',
  `email` varchar(100) DEFAULT NULL COMMENT 'メールアドレス',
  `postal_code` varchar(10) DEFAULT NULL COMMENT '郵便番号',
  `address1` varchar(200) DEFAULT NULL COMMENT '住所1',
  `address2` varchar(200) DEFAULT NULL COMMENT '住所2',
  `payment_terms` varchar(50) DEFAULT NULL COMMENT '支払条件',
  `currency` varchar(10) DEFAULT 'JPY' COMMENT '通貨',
  `remarks` text COMMENT '備考',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supplier_cd` (`supplier_cd`),
  KEY `idx_supplier_name` (`supplier_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='仕入先マスタ';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 010_create_process_routes.sql (original prefix 010)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for process_routes (工程ルートヘッダ)
-- ----------------------------
DROP TABLE IF EXISTS `process_routes`;
CREATE TABLE `process_routes` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ルートID',
  `route_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'ルートコード',
  `route_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'ルート名称',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '説明',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '使用フラグ',
  `is_default` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'デフォルトフラグ（製品に紐付く場合）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`, `route_cd`) USING BTREE,
  UNIQUE INDEX `route_cd`(`route_cd` ASC) USING BTREE
) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工程ルート（ヘッダ）' ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for process_route_steps (ルートステップ)
-- ----------------------------
DROP TABLE IF EXISTS `process_route_steps`;
CREATE TABLE `process_route_steps` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ルートステップID',
  `route_cd` varchar(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートID',
  `step_no` int NOT NULL COMMENT 'ステップ番号',
  `process_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '工程ID',
  `yield_percent` decimal(5, 2) NULL DEFAULT 100.00 COMMENT '歩留率（%）',
  `cycle_sec` decimal(5, 2) NULL DEFAULT 0.00 COMMENT '標準サイクル（秒）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 011_create_processes.sql (original prefix 011)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for processes (工程マスタ)
-- ----------------------------
DROP TABLE IF EXISTS `processes`;
CREATE TABLE `processes` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '工程ID',
  `process_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '工程コード',
  `process_name` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '工程名称',
  `short_name` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '略称／2〜3文字表示用',
  `category` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `is_outsource` tinyint(1) NOT NULL DEFAULT 0 COMMENT '外注フラグ(1=外注)',
  `default_cycle_sec` float NOT NULL DEFAULT 0 COMMENT '標準サイクルタイム(秒)',
  `default_yield` decimal(5, 3) NOT NULL DEFAULT 1.000 COMMENT '歩留(0〜1)',
  `capacity_unit` enum('pcs','kg','m') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'pcs' COMMENT '能力単位',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '備考',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `process_cd`(`process_cd` ASC) USING BTREE,
  INDEX `idx_category`(`category` ASC) USING BTREE,
  INDEX `idx_outsource`(`is_outsource` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '工程マスタ' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 012_create_destinations.sql (original prefix 012)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for destinations (納入先マスタ)
-- ----------------------------
DROP TABLE IF EXISTS `destinations`;
CREATE TABLE `destinations` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '納入先ID',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先名称',
  `customer_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '顧客CD（外部キー）',
  `carrier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '運送会社CD（外部キー）',
  `delivery_lead_time` int NULL DEFAULT 0 COMMENT '納入リードタイム（日）',
  `issue_type` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '自動' COMMENT '発行区分',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '電話番号',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '住所',
  `status` tinyint NULL DEFAULT 1 COMMENT '状态（1=启用, 0=停用）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日',
  `picked_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `destination_cd`(`destination_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '納入先マスタ' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for destination_holidays (納入先の休日設定)
-- ----------------------------
DROP TABLE IF EXISTS `destination_holidays`;
CREATE TABLE `destination_holidays` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `holiday_date` date NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_dest_date`(`destination_cd` ASC, `holiday_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '納入先の休日設定' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for destination_workdays (納入先臨時出勤日)
-- ----------------------------
DROP TABLE IF EXISTS `destination_workdays`;
CREATE TABLE `destination_workdays` (
  `id` int NOT NULL AUTO_INCREMENT,
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先マスタCD',
  `work_date` date NOT NULL COMMENT '土日の出勤日',
  `reason` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '理由',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_work_day`(`destination_cd` ASC, `work_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '納入先臨時出勤日マスタ（休日例外）' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 013_create_customers.sql (original prefix 013)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for customers (顧客マスタ)
-- ----------------------------
DROP TABLE IF EXISTS `customers`;
CREATE TABLE `customers` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '顧客ID',
  `customer_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '顧客CD',
  `customer_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '顧客名',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '電話番号',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '住所',
  `customer_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '顧客種別（corporate, individual, agency 等）',
  `status` tinyint NULL DEFAULT 1 COMMENT '状態（1=有効, 0=無効）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `customer_cd`(`customer_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '顧客マスタ' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 014_create_carriers.sql (original prefix 014)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for carriers (運送便マスタ)
-- ----------------------------
DROP TABLE IF EXISTS `carriers`;
CREATE TABLE `carriers` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '運送便ID',
  `carrier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '運送便CD',
  `carrier_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '運送便名称',
  `contact_person` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '連絡人',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '電話番号',
  `shipping_time` time NULL DEFAULT NULL COMMENT '出荷時間',
  `report_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '報告No',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '備考',
  `status` tinyint NULL DEFAULT 1 COMMENT '状態（1=有効, 0=無効）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `carrier_cd`(`carrier_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '運送便マスタ' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 015_create_machines.sql (original prefix 015)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for machines (設備マスタ)
-- ----------------------------
DROP TABLE IF EXISTS `machines`;
CREATE TABLE `machines` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '设备ID',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '设备CD',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '设备名称',
  `machine_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '设备种类（例：切断、焊接、检査等）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT 'active' COMMENT '状态（active/inactive/maintenance）',
  `available_from` time NULL DEFAULT '08:00:00' COMMENT '可用开始时间',
  `available_to` time NULL DEFAULT '17:00:00' COMMENT '可用结束时间',
  `calendar_id` int NULL DEFAULT NULL COMMENT '所属カレンダーID（处理休假）',
  `efficiency` decimal(5, 2) NULL DEFAULT 100.00 COMMENT '效率（基准为100）',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '备注',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `machine_cd`(`machine_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin COMMENT = '設備マスタ' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 016_order_monthly_new_schema.sql (original prefix 016)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ================================================================
-- 月別受注テーブル 新スキーマ適用
-- order_monthly: 納入先・製品・内示中心の設計、order_id トリガー生成
-- Version: 016
-- ================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- 日別受注の外部キー依存のため先に削除（必要に応じてデータ退避後に実行）
DROP TABLE IF EXISTS `order_daily`;

DROP TRIGGER IF EXISTS `trg_order_monthly_before_insert`;
DROP TABLE IF EXISTS `order_monthly`;

-- ================================================================
-- 月別受注テーブル (新スキーマ)
-- ================================================================
CREATE TABLE `order_monthly` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '月別受注ID',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先名',
  `year` int NOT NULL COMMENT '年',
  `month` int NOT NULL COMMENT '月',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品別名',
  `product_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '量産品' COMMENT '製品種別（量産品/試作品/補給品/その他）',
  `forecast_units` int NULL DEFAULT 0 COMMENT '内示本数',
  `forecast_total_units` int NULL DEFAULT 0 COMMENT '日内示合計',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '受注ID（トリガーで上書き）',
  `forecast_diff` int NULL DEFAULT 0 COMMENT '内示差異（日内示合計-内示本数 ）',
  PRIMARY KEY (`id`, `order_id`) USING BTREE,
  UNIQUE INDEX `uq_order_monthly_order_id`(`order_id` ASC) USING BTREE,
  INDEX `idx_order_monthly_destination`(`destination_cd` ASC, `year` ASC, `month` ASC) USING BTREE,
  INDEX `idx_order_monthly_product`(`product_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '月別受注テーブル' ROW_FORMAT = DYNAMIC;

-- ================================================================
-- トリガー: INSERT 時に order_id を自動生成
-- ================================================================
DROP TRIGGER IF EXISTS `trg_order_monthly_before_insert`;
delimiter ;;
CREATE TRIGGER `trg_order_monthly_before_insert` BEFORE INSERT ON `order_monthly` FOR EACH ROW BEGIN
  DECLARE typeSuffix CHAR(1);

  SET typeSuffix = CASE NEW.product_type
    WHEN '試作品' THEN '1'
    WHEN '別注品' THEN '2'
    WHEN '補給品' THEN '3'
    WHEN 'サンプル品' THEN '4'
    WHEN '代替品' THEN '5'
    WHEN '返却品' THEN '6'
    WHEN 'その他' THEN '7'
    ELSE '0'
  END;

  SET NEW.order_id = CONCAT(
    NEW.year,
    LPAD(NEW.month, 2, '0'),
    NEW.destination_cd,
    NEW.product_cd,
    typeSuffix
  );
END;;
delimiter ;

-- ================================================================
-- 日別受注テーブル 再作成（order_monthly.id への FK）
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

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 017_order_daily_new_schema.sql (original prefix 017)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ================================================================
-- 日別受注テーブル 新スキーマ
-- monthly_order_id → order_monthly.order_id (varchar) を参照
-- Version: 017
-- ================================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `order_daily`;

CREATE TABLE `order_daily` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '日別受注ID',
  `monthly_order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '月別受注ID（order_monthly.order_id）',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '納入先名',
  `data` date NOT NULL COMMENT '年月日',
  `weekday` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '曜日（日/月/火/水/木/金/土）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品別名',
  `forecast_units` int NULL DEFAULT 0 COMMENT '内示本数',
  `confirmed_boxes` int NULL DEFAULT 0 COMMENT '確定箱数',
  `confirmed_units` int NULL DEFAULT 0 COMMENT '確定本数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '未出荷' COMMENT '日別受注ステータス',
  `remarks` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '備考',
  `unit_per_box` int NULL DEFAULT 0 COMMENT '1箱あたりの個数',
  `batch_id` int NULL DEFAULT NULL COMMENT '対応する生産バッチID',
  `batch_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'バッチ番号（表示用）',
  `supply_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `fulfilled_from_stock` int NULL DEFAULT 0,
  `fulfilled_from_wip` int NULL DEFAULT 0,
  `product_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `confirmed` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否已确认（0:未确认,1:已确认）',
  `confirmed_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '确认人',
  `confirmed_at` datetime NULL DEFAULT NULL COMMENT '确认时间',
  `delivery_date` date NULL DEFAULT NULL COMMENT '納入日（交货日期）',
  `shipping_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `fk_order_daily_monthly`(`monthly_order_id` ASC) USING BTREE,
  INDEX `idx_order_batch_id`(`batch_id` ASC) USING BTREE,
  INDEX `idx_order_daily_data`(`data` ASC) USING BTREE,
  CONSTRAINT `order_daily_ibfk_1` FOREIGN KEY (`monthly_order_id`) REFERENCES `order_monthly` (`order_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC COMMENT = '日別受注';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 018_order_monthly.sql (original prefix 018)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 月別受注テーブル（受注管理）
-- order_id は BEFORE INSERT トリガーで自動採番

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TRIGGER IF EXISTS `trg_order_monthly_before_insert`;
DROP TABLE IF EXISTS `order_monthly`;

CREATE TABLE `order_monthly` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '月订单ID',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先名',
  `year` int NOT NULL COMMENT '年',
  `month` int NOT NULL COMMENT '月',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品別名',
  `product_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '量産品' COMMENT '製品種別（量産品/試作品/補給品/その他）',
  `forecast_units` int NULL DEFAULT 0 COMMENT '内示本数',
  `forecast_total_units` int NULL DEFAULT 0 COMMENT '日内示合計',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '受注ID',
  `forecast_diff` int NULL DEFAULT 0 COMMENT '内示差異（日内示合計-内示本数 ）',
  PRIMARY KEY (`id`, `order_id`) USING BTREE,
  UNIQUE INDEX `uq_order_monthly_order_id`(`order_id` ASC) USING BTREE,
  INDEX `idx_order_monthly_destination`(`destination_cd` ASC, `year` ASC, `month` ASC) USING BTREE,
  INDEX `idx_order_monthly_product`(`product_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '月別受注テーブル' ROW_FORMAT = DYNAMIC;

DELIMITER ;;
CREATE TRIGGER `trg_order_monthly_before_insert` BEFORE INSERT ON `order_monthly` FOR EACH ROW BEGIN
  DECLARE typeSuffix CHAR(1);

  SET typeSuffix = CASE NEW.product_type
    WHEN '試作品' THEN '1'
    WHEN '別注品' THEN '2'
    WHEN '補給品' THEN '3'
    WHEN 'サンプル品' THEN '4'
    WHEN '代替品' THEN '5'
    WHEN '返却品' THEN '6'
    WHEN 'その他' THEN '7'
    ELSE '0'
  END;

  SET NEW.order_id = CONCAT(
    NEW.year,
    LPAD(NEW.month, 2, '0'),
    NEW.destination_cd,
    NEW.product_cd,
    typeSuffix
  );
END;;
DELIMITER ;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 019_rename_products_delivery_destination_to_destination_cd.sql (original prefix 019)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- products.delivery_destination_cd を destination_cd にリネーム（既存DB用）
SET NAMES utf8mb4;

ALTER TABLE `products`
  CHANGE COLUMN `delivery_destination_cd` `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '納入先CD（外部キー）';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 020_order_daily.sql (original prefix 020)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ================================================================
-- 日受注 order_daily（用户提供样式）
-- Version: 020
-- ================================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `order_daily`;
CREATE TABLE `order_daily`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '日订单ID',
  `monthly_order_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '月订单ID（order_monthly的order_id）',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '納入先CD',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '納入先名',
  `date` date NOT NULL COMMENT '年月日',
  `weekday` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '曜日（日/月/火/水/木/金/土）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品別名',
  `forecast_units` int NULL DEFAULT 0 COMMENT '内示本数',
  `confirmed_boxes` int NULL DEFAULT 0 COMMENT '確定箱数',
  `confirmed_units` int NULL DEFAULT 0 COMMENT '確定本数',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '未出荷' COMMENT '日別受注ステータス',
  `remarks` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '備考',
  `unit_per_box` int NULL DEFAULT 0 COMMENT '1箱あたりの個数',
  `batch_id` int NULL DEFAULT NULL COMMENT '対応する生産バッチID',
  `batch_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'バッチ番号（表示用）',
  `supply_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `fulfilled_from_stock` int NULL DEFAULT 0,
  `fulfilled_from_wip` int NULL DEFAULT 0,
  `product_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `confirmed` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否已确认（0:未确认,1:已确认）',
  `confirmed_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '确认人',
  `confirmed_at` datetime NULL DEFAULT NULL COMMENT '确认时间',
  `delivery_date` date NULL DEFAULT NULL COMMENT '納入日（交货日期）',
  `shipping_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `fk_order_daily_monthly`(`monthly_order_id` ASC) USING BTREE,
  INDEX `idx_order_batch_id`(`batch_id` ASC) USING BTREE,
  CONSTRAINT `order_daily_ibfk_1` FOREIGN KEY (`monthly_order_id`) REFERENCES `order_monthly` (`order_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 021_order_daily_rename_data_to_date.sql (original prefix 021)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- order_daily テーブルの data カラムを date にリネーム
-- Version: 021

SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `order_daily`
  CHANGE COLUMN `data` `date` date NOT NULL COMMENT '年月日';

-- インデックス名が idx_order_daily_data の場合はリネーム（017 で定義されている場合）
-- MySQL では CHANGE COLUMN でカラム名変更してもインデックスは自動で付くので、必要なら別途 DROP INDEX + CREATE INDEX

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 022_product_route_steps.sql (original prefix 022)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for product_route_steps (製品別工程ルートステップ)
-- ----------------------------
DROP TABLE IF EXISTS `product_route_step_machines`;
DROP TABLE IF EXISTS `product_route_steps`;

CREATE TABLE `product_route_steps` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品CD',
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートCD',
  `step_no` int NOT NULL COMMENT '順番',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '工程CD',
  `machine_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '設備ID',
  `standard_cycle_time` decimal(10, 2) NULL DEFAULT NULL COMMENT '標準サイクルタイム(秒)',
  `setup_time` decimal(10, 2) NULL DEFAULT NULL COMMENT '段取り時間(秒)',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_product_route_step`(`product_cd` ASC, `route_cd` ASC, `step_no` ASC) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 CHARACTER SET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品別工程ルートステップ' ROW_FORMAT=DYNAMIC;

-- ----------------------------
-- Table structure for product_route_step_machines (製品別工程ステップ設備)
-- ----------------------------
CREATE TABLE `product_route_step_machines` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `step_no` int NOT NULL,
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `process_time_sec` decimal(4, 2) NOT NULL DEFAULT 0.00,
  `setup_time` int NOT NULL DEFAULT 0,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_step`(`product_cd` ASC, `route_cd` ASC, `step_no` ASC) USING BTREE,
  INDEX `idx_machine`(`machine_cd` ASC) USING BTREE,
  CONSTRAINT `product_route_step_machines_ibfk_1` FOREIGN KEY (`machine_cd`) REFERENCES `machines` (`machine_cd`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 CHARACTER SET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品別工程ステップ設備' ROW_FORMAT=DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 023_stock_transaction_logs.sql (original prefix 023)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 在庫受払履歴 (stock_transaction_logs)
DROP TABLE IF EXISTS `stock_transaction_logs`;

CREATE TABLE `stock_transaction_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '在庫操作履歴ID (BIGINT推奨)',
  `stock_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '在庫種別 (製品,材料,部品,仕掛品)',
  `transaction_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '操作種別 (入庫,出庫,実績、不良、廃棄、保留、調整、初期)',
  `target_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '品目コード',
  `location_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '保管場所コード',
  `lot_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ロット番号 (重要)',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '工程コード',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '設備コード',
  `quantity` decimal(18, 4) NOT NULL COMMENT '操作数量 (増減符号付き推奨: 入庫+10, 出庫-10)',
  `unit` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '単位 (kg, pcs, m)',
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '関連伝票No (受注No, 発注No, 製造指図No)',
  `related_log_id` bigint NULL DEFAULT NULL COMMENT '取消時の元ログIDなど',
  `operator_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '操作担当者ID',
  `operator_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '担当者名(ログとして名前も残すのはアリ)',
  `transaction_time` datetime(3) NOT NULL COMMENT '操作日時 (ミリ秒まで記録推奨)',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
  `source_file` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '来源文件名',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '備考',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_target_time`(`target_cd` ASC, `transaction_time` ASC) USING BTREE,
  INDEX `idx_location_target`(`location_cd` ASC, `target_cd` ASC) USING BTREE,
  INDEX `idx_lot`(`lot_no` ASC, `target_cd` ASC) USING BTREE,
  INDEX `idx_order`(`order_no` ASC) USING BTREE,
  INDEX `idx_source_file`(`source_file` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 119 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '在庫受払履歴' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 024_material_logs_and_inspection_master.sql (original prefix 024)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 材料检收日志 (material_logs) 与 材料检验主数据 (material_inspection_master)
-- 供 BT-data 受信文件监视写入 Material_*.csv 使用
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 材料检验主数据（Maruiti 等解析用）
-- ----------------------------
CREATE TABLE IF NOT EXISTS `material_inspection_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `inspection_cd` varchar(50) NOT NULL COMMENT '检验CD',
  `inspection_standard` varchar(200) DEFAULT NULL COMMENT '检验规格/标准名',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_inspection_cd` (`inspection_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='材料检验主数据';

-- ----------------------------
-- 材料日志 (BT-data 受信同步)
-- ----------------------------
DROP TABLE IF EXISTS `material_logs`;
CREATE TABLE `material_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item` varchar(100) NOT NULL COMMENT '项目/品种标识',
  `log_date` date NOT NULL COMMENT '日志日期',
  `log_time` varchar(20) DEFAULT NULL COMMENT '日志时间',
  `hd_no` varchar(50) DEFAULT NULL COMMENT 'HD No',
  `remarks` varchar(500) DEFAULT NULL,
  `material_cd` varchar(50) DEFAULT NULL,
  `material_name` varchar(200) DEFAULT NULL,
  `process_cd` varchar(50) DEFAULT NULL,
  `manufacture_no` varchar(100) DEFAULT NULL,
  `manufacture_date` date DEFAULT NULL,
  `pieces_per_bundle` int DEFAULT NULL,
  `length` varchar(50) DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `bundle_quantity` int DEFAULT NULL,
  `magnetic` tinyint DEFAULT 1,
  `appearance` tinyint DEFAULT 1,
  `outer_diameter1` decimal(12,4) DEFAULT NULL,
  `outer_diameter2` decimal(12,4) DEFAULT NULL,
  `supplier` varchar(200) DEFAULT NULL,
  `material_quality` varchar(100) DEFAULT NULL,
  `note` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_item` (`item`),
  KEY `idx_log_date` (`log_date`),
  KEY `idx_manufacture` (`manufacture_no`,`log_date`,`log_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='材料检收日志(BT-data受信)';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 025_product_process_bom.sql (original prefix 025)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 製品工程BOM (Product Process BOM)
CREATE TABLE IF NOT EXISTS `product_process_bom` (
  `product_cd` int NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品名',
  `min_stock_days` int NULL DEFAULT NULL COMMENT '最低在庫日数',
  `safety_stock_days` int NULL DEFAULT NULL COMMENT '安全在庫日数',
  `material_process` tinyint(1) NULL DEFAULT NULL COMMENT '材料 (工程)',
  `material_process_lt` int NULL DEFAULT NULL COMMENT '材料工程LT',
  `cuting_process` tinyint(1) NULL DEFAULT NULL COMMENT '切断 (工程)',
  `cuting_process_lt` int NULL DEFAULT NULL COMMENT '切断工程LT',
  `chamfering_process` tinyint(1) NULL DEFAULT NULL COMMENT '面取 (工程)',
  `chamfering_process_lt` int NULL DEFAULT NULL COMMENT '面取工程LT',
  `swaging_process` tinyint(1) NULL DEFAULT NULL COMMENT 'SW (工程)',
  `swaging_process_lt` int NULL DEFAULT NULL COMMENT 'SW工程LT',
  `forming_process` tinyint(1) NULL DEFAULT NULL COMMENT '成型 (工程)',
  `forming_process_lt` int NULL DEFAULT NULL COMMENT '成型工程LT',
  `plating_process` tinyint(1) NULL DEFAULT NULL COMMENT 'メッキ (工程)',
  `plating_process_lt` int NULL DEFAULT NULL COMMENT 'メッキ工程LT',
  `outsourced_plating_process` tinyint(1) NULL DEFAULT NULL COMMENT '外注メッキ (工程)',
  `outsourced_plating_process_lt` int NULL DEFAULT NULL COMMENT '外注メッキ工程LT',
  `welding_process` tinyint(1) NULL DEFAULT NULL COMMENT '溶接 (工程)',
  `welding_process_lt` int NULL DEFAULT NULL COMMENT '溶接工程LT',
  `outsourced_welding_process` tinyint(1) NULL DEFAULT NULL COMMENT '外注溶接 (工程)',
  `outsourced_welding_process_lt` int NULL DEFAULT NULL COMMENT '外注溶接工程LT',
  `inspection_process` tinyint(1) NULL DEFAULT NULL COMMENT '検査 (工程)',
  `inspection_process_lt` int NULL DEFAULT NULL COMMENT '検査工程LT',
  `outsourced_warehouse_process` tinyint(1) NULL DEFAULT NULL COMMENT '外注倉庫 (工程)',
  `outsourced_warehouse_process_lt` int NULL DEFAULT NULL COMMENT '外注検査工程LT',
  `pre_plating_welding` tinyint(1) NULL DEFAULT NULL COMMENT 'メッキ前溶接 (工程)',
  `post_inspection_welding` tinyint(1) NULL DEFAULT NULL COMMENT '検査後溶接 (工程)',
  `post_inspection_welding_lt` int NULL DEFAULT NULL COMMENT '検査後溶接工程LT',
  `is_discontinued` tinyint(1) NULL DEFAULT NULL COMMENT '終息',
  PRIMARY KEY (`product_cd`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '製品工程BOM (Product Process BOM)' ROW_FORMAT = Dynamic;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 026_production_plan_excel_tables.sql (original prefix 026)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 生産計画 Excel 取込用テーブル（監視ファイル 加工計画/溶接計画 用）
-- production_plan_updates: 計画更新
-- production_plan_schedules: 加工状況/溶接状況
-- production_plan_rate: 操業度

DROP TABLE IF EXISTS `production_plan_rate`;
DROP TABLE IF EXISTS `production_plan_schedules`;
DROP TABLE IF EXISTS `production_plan_updates`;

CREATE TABLE `production_plan_updates` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) NOT NULL COMMENT '来源文件名',
  `processed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `plan_date` date DEFAULT NULL COMMENT '生産日',
  `quantity` decimal(18,4) DEFAULT NULL COMMENT '生産数',
  `machine_name` varchar(100) DEFAULT NULL,
  `machine_cd` varchar(50) DEFAULT NULL,
  `process_name` varchar(50) DEFAULT NULL COMMENT '成型/溶接',
  `operator` varchar(100) DEFAULT NULL COMMENT '生産準',
  `product_name` varchar(200) DEFAULT NULL,
  `product_cd` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ppu_file` (`file_name`),
  KEY `idx_ppu_plan_date` (`plan_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='計画更新(Excel取込)';

CREATE TABLE `production_plan_schedules` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) NOT NULL,
  `processed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `machine_name` varchar(100) DEFAULT NULL,
  `product_name` varchar(200) DEFAULT NULL,
  `production_order` varchar(100) DEFAULT NULL,
  `planned_quantity` decimal(18,4) DEFAULT NULL,
  `production_start_date` date DEFAULT NULL,
  `production_end_date` date DEFAULT NULL,
  `actual_production` decimal(18,4) DEFAULT NULL,
  `variance` decimal(18,4) DEFAULT NULL,
  `achievement_rate` decimal(10,2) DEFAULT NULL,
  `total_production_time` decimal(18,2) DEFAULT NULL,
  `operation_variance` varchar(100) DEFAULT NULL,
  `material_lot_count` int DEFAULT NULL,
  `material_name` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pps_file` (`file_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='加工/溶接状況(Excel取込)';

CREATE TABLE `production_plan_rate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) NOT NULL,
  `processed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `machine_cd` varchar(50) DEFAULT NULL,
  `machine_name` varchar(100) DEFAULT NULL,
  `operation_variance` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_ppr_file` (`file_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='操業度(Excel取込)';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 027_product_machine_config.sql (original prefix 027)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 製品機器設定管理テーブル
CREATE TABLE IF NOT EXISTS `product_machine_config` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品コード',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `cutting_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '切断機器',
  `chamfering_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '面取機器',
  `molding_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '成型機器',
  `plating_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'メッキ機器',
  `welding_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '溶接機器',
  `inspector_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '検査機器',
  `outsourced_plating_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '外注メッキ機器',
  `outsourced_welding_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '外注溶接機器',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_product_name`(`product_name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '製品機器設定管理テーブル' ROW_FORMAT = Dynamic;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 028_shipping_log.sql (original prefix 028)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- PickingLog.csv 監視用：出荷ピッキングログ（fileWatcherService.js と同等）
-- UNIQUE(picking_no, product_code, date) で ON DUPLICATE KEY UPDATE に対応

CREATE TABLE IF NOT EXISTS shipping_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  project VARCHAR(100) DEFAULT '',
  date DATE NULL,
  datetime DATETIME NULL,
  model_no VARCHAR(100) DEFAULT '',
  person_in_charge VARCHAR(100) DEFAULT '',
  picking_no VARCHAR(100) DEFAULT '',
  product_name VARCHAR(300) DEFAULT '',
  product_code VARCHAR(100) DEFAULT '',
  product_name_2 VARCHAR(300) DEFAULT '',
  quantity INT DEFAULT 0,
  shipping_quantity INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_picking_product_date (picking_no, product_code, date),
  KEY idx_date (date),
  KEY idx_picking_no (picking_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='出荷ピッキングログ（PickingLog.csv取込）';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 029_destination_groups.sql (original prefix 029)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 納入先分组管理表（出荷構成表等で使用）
-- 既にテーブルがある場合はスキップ（DROP しない）
CREATE TABLE IF NOT EXISTS `destination_groups` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键，自增',
  `page_key` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '页面唯一标识，用于区分不同页面的分组集合',
  `group_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分组名称，用户自定义',
  `destinations` json NOT NULL COMMENT '分组内的纳入先列表，JSON格式存储',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间戳',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间戳',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_page_key`(`page_key` ASC) USING BTREE,
  INDEX `idx_updated_at`(`updated_at` ASC) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='納入先分组管理表' ROW_FORMAT=Dynamic;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 030_shipping_items.sql (original prefix 030)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 出荷明細テーブル（出荷構成表）
CREATE TABLE IF NOT EXISTS `shipping_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `shipping_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '出荷番号',
  `shipping_date` date NOT NULL COMMENT '出荷日',
  `delivery_date` date NULL DEFAULT NULL COMMENT '納入日',
  `destination_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '納入先コード',
  `destination_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '納入先名',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品コード',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '製品名',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '製品別名/納入日など追加情報',
  `box_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL COMMENT '箱種',
  `confirmed_boxes` int NOT NULL DEFAULT 0 COMMENT '箱数',
  `confirmed_units` int NOT NULL DEFAULT 0 COMMENT '出荷数量',
  `unit` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '本' COMMENT '単位',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '未発行' COMMENT '状態（未発行/発行済/出荷済/キャンセル）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登録日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `shipping_no_p` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  PRIMARY KEY (`id`, `shipping_no_p`) USING BTREE,
  UNIQUE INDEX `uq_shipping_no_p`(`shipping_no_p` ASC) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='出荷管理' ROW_FORMAT=DYNAMIC;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 031_shipping_records.sql (original prefix 031)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 出荷印刷記録テーブル
CREATE TABLE IF NOT EXISTS `shipping_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `shipping_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '出荷番号（例：20250611-D001-007）',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `shipping_no`(`shipping_no` ASC) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=DYNAMIC;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 032_picking_list.sql (original prefix 032)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ピッキング用リスト（shipping_items の当日以降を同期）
CREATE TABLE IF NOT EXISTS `picking_list` (
  `id` int NOT NULL AUTO_INCREMENT,
  `shipping_no_p` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `shipping_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  `confirmed_boxes` int NOT NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_shipping_product` (`shipping_no_p`, `product_cd`) USING BTREE,
  KEY `idx_shipping_no` (`shipping_no`),
  KEY `idx_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin ROW_FORMAT=DYNAMIC;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 033_print_history.sql (original prefix 033)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 印刷履歴（出荷報告・カレンダー等）
CREATE TABLE IF NOT EXISTS `print_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `report_type` varchar(50) NOT NULL,
  `report_title` varchar(200) DEFAULT NULL,
  `filters` json DEFAULT NULL,
  `record_count` int DEFAULT 0,
  `status` varchar(20) DEFAULT NULL,
  `error_message` text,
  `user_name` varchar(100) DEFAULT NULL,
  `printed_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_report_type` (`report_type`),
  KEY `idx_printed_at` (`printed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 034_equipment_efficiency.sql (original prefix 034)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 設備能率管理テーブル（equipment_efficiency）
-- 設備ごとの加工製品別能率設定・管理

CREATE TABLE IF NOT EXISTS `equipment_efficiency` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `machine_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備コード',
  `machines_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備名',
  `product_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品コード',
  `product_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品名',
  `efficiency_rate` decimal(10, 1) NULL DEFAULT 0.0 COMMENT '能率（数値）本/H',
  `step_time` int NULL DEFAULT NULL COMMENT '段取時間（分）',
  `unit` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '単位（例：件/時間、個/分）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `status` tinyint NULL DEFAULT NULL COMMENT '終息',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_equipment_product` (`machine_cd`, `product_cd`),
  KEY `idx_equipment_code` (`machine_cd`),
  KEY `idx_product_code` (`product_cd`),
  KEY `idx_equipment_product` (`machine_cd`, `product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備能率管理テーブル' ROW_FORMAT=Dynamic;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 035_machine_work_time_config.sql (original prefix 035)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 設備運行時間設定（成型指示画面の時間帯 17-19, 19-21, 6-8 用）

CREATE TABLE IF NOT EXISTS `machine_work_time_config` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `machine_cd` varchar(50) NOT NULL COMMENT '設備コード',
  `machine_name` varchar(100) DEFAULT NULL COMMENT '設備名',
  `time_slot_17_19` tinyint NOT NULL DEFAULT 0 COMMENT '17-19時 稼働(1)/非稼働(0)',
  `time_slot_19_21` tinyint NOT NULL DEFAULT 0 COMMENT '19-21時 稼働(1)/非稼働(0)',
  `time_slot_6_8` tinyint NOT NULL DEFAULT 0 COMMENT '6-8時 稼働(1)/非稼働(0)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_machine_cd` (`machine_cd`),
  KEY `idx_machine_name` (`machine_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備運行時間設定';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 036_production_plan_baselines.sql (original prefix 036)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 生産計画月次ベースライン（比較基準の固定化）
CREATE TABLE IF NOT EXISTS `production_plan_baselines` (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `baseline_month` date NOT NULL COMMENT '基準月份(每月第一天)',
  `snapshot_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '快照生成時間',
  `plan_date` date NOT NULL COMMENT '計画日',
  `machine_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '設備名',
  `product_cd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '製品名',
  `process_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '工程名',
  `plan_quantity` decimal(15, 2) NOT NULL DEFAULT 0.00 COMMENT '計画数量',
  `actual_quantity` decimal(15, 2) NOT NULL DEFAULT 0.00 COMMENT '実績数量',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uniq_baseline_month_day_proc` (`baseline_month`,`plan_date`,`process_name`) USING BTREE,
  KEY `idx_baseline_month` (`baseline_month`),
  KEY `idx_plan_date` (`plan_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生産計画月次ベースライン' ROW_FORMAT=Dynamic;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 037_production_summarys_safety_stock.sql (original prefix 037)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_summarys に「安全在庫」カラムを追加
ALTER TABLE `production_summarys`
  ADD COLUMN `safety_stock` int NULL DEFAULT 0 COMMENT '安全在庫' AFTER `forecast_quantity`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 038_distributed_locks.sql (original prefix 038)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 分散ロック（他端末との同時一括更新防止）
CREATE TABLE IF NOT EXISTS `distributed_locks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `lock_key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `lock_value` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` timestamp NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `lock_key` (`lock_key` ASC) USING BTREE,
  INDEX `idx_lock_key` (`lock_key` ASC) USING BTREE,
  INDEX `idx_expires_at` (`expires_at` ASC) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=Dynamic;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 039_add_printed_at_to_print_history.sql (original prefix 039)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- Add printed_at column to print_history table if it doesn't exist
-- This fixes the "Unknown column 'printed_at'" error

-- Check if column exists and add it if missing
SET @dbname = DATABASE();
SET @tablename = 'print_history';
SET @columnname = 'printed_at';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' datetime DEFAULT CURRENT_TIMESTAMP AFTER user_name')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add index on printed_at if it doesn't exist
SET @indexname = 'idx_printed_at';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (index_name = @indexname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD INDEX ', @indexname, ' (', @columnname, ')')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 040_outsourcing_tables.sql (original prefix 040)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 外注管理関連テーブル（支給材料・メッキ・溶接注文/受入/在庫）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- outsourcing_suppliers 外注先マスタ
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_suppliers`;
CREATE TABLE `outsourcing_suppliers` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '外注先ID',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `supplier_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先名',
  `supplier_type` enum('plating','welding','cutting','forming','parts_processing') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'plating' COMMENT '外注種別（メッキ/溶接/切断/成型/部品加工）',
  `postal_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '郵便番号',
  `address` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '住所',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '電話番号',
  `fax` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'FAX番号',
  `contact_person` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '担当者名',
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'メールアドレス',
  `payment_terms` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '支払条件',
  `lead_time_days` int NULL DEFAULT 7 COMMENT '標準リードタイム（日）',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_supplier_type`(`supplier_type` ASC) USING BTREE,
  INDEX `idx_is_active`(`is_active` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注先マスタ' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_process_products 外注工程製品マスタ
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_process_products`;
CREATE TABLE `outsourcing_process_products` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `process_type` enum('cutting','forming','plating','welding','inspection','processing') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程種別',
  `supplier_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `supplier_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '外注先名',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `specification` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `unit_price` decimal(12, 2) NULL DEFAULT 0.00 COMMENT '単価',
  `delivery_lead_time` int NULL DEFAULT 7 COMMENT '納入リードタイム（日）',
  `delivery_location` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '納入場所',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '区分',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '内容',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '更新者',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_process_supplier_product`(`process_type` ASC, `supplier_cd` ASC, `product_cd` ASC) USING BTREE,
  INDEX `idx_process_type`(`process_type` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_is_active`(`is_active` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注工程製品マスタ' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_supplied_material_stock 外注先支給材料在庫
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_supplied_material_stock`;
CREATE TABLE `outsourcing_supplied_material_stock` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料コード',
  `material_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '材料名',
  `spec` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '個' COMMENT '単位',
  `unit_weight` decimal(10, 4) NULL DEFAULT 0.0000 COMMENT '単重（kg）',
  `issued_qty` decimal(12, 3) NULL DEFAULT 0.000 COMMENT '支給累計数量',
  `used_qty` decimal(12, 3) NULL DEFAULT 0.000 COMMENT '使用累計数量',
  `stock_qty` decimal(12, 3) GENERATED ALWAYS AS ((`issued_qty` - `used_qty`)) STORED COMMENT '現在庫数量' NULL,
  `min_stock` decimal(12, 3) NULL DEFAULT 0.000 COMMENT '最低在庫数',
  `last_issue_date` date NULL DEFAULT NULL COMMENT '最終支給日',
  `last_usage_date` date NULL DEFAULT NULL COMMENT '最終使用日',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_supplier_material`(`supplier_cd` ASC, `material_cd` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_material_cd`(`material_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注先支給材料在庫' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_material_transactions 支給材料入出庫履歴
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_material_transactions`;
CREATE TABLE `outsourcing_material_transactions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '取引ID',
  `transaction_date` date NOT NULL COMMENT '取引日',
  `transaction_type` enum('issue','usage','return') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '取引種別（支給/使用/返却）',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料コード',
  `material_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '材料名',
  `related_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '関連番号',
  `quantity` decimal(12, 3) NOT NULL COMMENT '数量',
  `stock_after` decimal(12, 3) NULL DEFAULT NULL COMMENT '取引後在庫',
  `operator` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '担当者',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_transaction_date`(`transaction_date` ASC) USING BTREE,
  INDEX `idx_transaction_type`(`transaction_type` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_material_cd`(`material_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '支給材料入出庫履歴' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_material_issues 支給材料出庫
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_material_issues`;
CREATE TABLE `outsourcing_material_issues` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '支給ID',
  `issue_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '支給番号',
  `issue_date` date NOT NULL COMMENT '出庫日',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `related_order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '関連注文番号',
  `related_order_type` enum('plating','welding') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '関連注文種別',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料コード',
  `material_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '材料名',
  `spec` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `quantity` decimal(12, 3) NOT NULL COMMENT '支給数量',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '個' COMMENT '単位',
  `unit_weight` decimal(10, 4) NULL DEFAULT 0.0000 COMMENT '単重（kg）',
  `total_weight` decimal(14, 4) GENERATED ALWAYS AS ((`quantity` * `unit_weight`)) STORED COMMENT '総重量（kg）' NULL,
  `status` enum('preparing','issued','returned') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'preparing' COMMENT '状態',
  `operator` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '担当者',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `issue_no`(`issue_no` ASC) USING BTREE,
  INDEX `idx_issue_no`(`issue_no` ASC) USING BTREE,
  INDEX `idx_issue_date`(`issue_date` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_material_cd`(`material_cd` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '支給材料出庫' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_material_usages 支給材料使用報告
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_material_usages`;
CREATE TABLE `outsourcing_material_usages` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '使用ID',
  `usage_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '報告番号',
  `usage_date` date NOT NULL COMMENT '使用日',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `related_order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '関連注文番号',
  `related_order_type` enum('plating','welding') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '関連注文種別',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料コード',
  `material_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '材料名',
  `usage_qty` decimal(12, 3) NOT NULL COMMENT '使用数量',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '個' COMMENT '単位',
  `unit_weight` decimal(10, 4) NULL DEFAULT 0.0000 COMMENT '単重（kg）',
  `usage_weight` decimal(14, 4) GENERATED ALWAYS AS ((`usage_qty` * `unit_weight`)) STORED COMMENT '使用重量（kg）' NULL,
  `product_qty` int NULL DEFAULT 0 COMMENT '製品数量',
  `yield_rate` decimal(5, 2) NULL DEFAULT NULL COMMENT '歩留率（%）',
  `reporter` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '報告者',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `usage_no`(`usage_no` ASC) USING BTREE,
  INDEX `idx_usage_no`(`usage_no` ASC) USING BTREE,
  INDEX `idx_usage_date`(`usage_date` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_material_cd`(`material_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '支給材料使用報告' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_stock_transactions 外注入出庫履歴
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_stock_transactions`;
CREATE TABLE `outsourcing_stock_transactions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '取引ID',
  `transaction_date` date NOT NULL COMMENT '取引日',
  `transaction_type` enum('receive','issue') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '取引種別（入庫/出庫）',
  `process_type` enum('plating','welding') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '加工種別',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `related_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '関連番号（受入番号/出庫番号）',
  `quantity` int NOT NULL COMMENT '数量',
  `stock_after` int NULL DEFAULT NULL COMMENT '取引後在庫',
  `operator` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '担当者',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_transaction_date`(`transaction_date` ASC) USING BTREE,
  INDEX `idx_transaction_type`(`transaction_type` ASC) USING BTREE,
  INDEX `idx_process_type`(`process_type` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注入出庫履歴' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_plating_orders 外注メッキ注文
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_plating_orders`;
CREATE TABLE `outsourcing_plating_orders` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '注文ID',
  `order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '注文番号',
  `order_date` date NOT NULL COMMENT '注文日',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `plating_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'メッキ種類',
  `quantity` int NOT NULL COMMENT '注文数量',
  `unit` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '個' COMMENT '単位',
  `unit_price` decimal(12, 2) NULL DEFAULT 0.00 COMMENT '単価',
  `amount` decimal(14, 2) GENERATED ALWAYS AS ((`quantity` * `unit_price`)) STORED COMMENT '金額' NULL,
  `delivery_date` date NULL DEFAULT NULL COMMENT '納期',
  `delivery_location` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '納入場所',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '区分',
  `content` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '内容',
  `specification` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `received_qty` int NULL DEFAULT 0 COMMENT '入庫済数量',
  `status` enum('pending','ordered','partial','completed','cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'pending' COMMENT '状態',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '作成者',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `order_no`(`order_no` ASC) USING BTREE,
  INDEX `idx_order_no`(`order_no` ASC) USING BTREE,
  INDEX `idx_order_date`(`order_date` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_delivery_date`(`delivery_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注メッキ注文' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_plating_stock 外注メッキ品在庫
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_plating_stock`;
CREATE TABLE `outsourcing_plating_stock` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品名',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先CD',
  `plating_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'メッキ種類',
  `ordered_qty` int NULL DEFAULT 0 COMMENT '発注累計数量',
  `received_qty` int NULL DEFAULT 0 COMMENT '入庫累計数量',
  `used_qty` int NULL DEFAULT 0 COMMENT '出庫累計数量',
  `stock_qty` int GENERATED ALWAYS AS ((`ordered_qty` - `used_qty`)) STORED COMMENT '現在庫数量' NULL,
  `pending_qty` int NULL DEFAULT 0 COMMENT '入庫予定数量',
  `min_stock` int NULL DEFAULT 0 COMMENT '最低在庫数',
  `last_receive_date` date NULL DEFAULT NULL COMMENT '最終入庫日',
  `last_issue_date` date NULL DEFAULT NULL COMMENT '最終出庫日',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_product_supplier`(`product_cd` ASC, `supplier_cd` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注メッキ品在庫' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_plating_receivings 外注メッキ受入
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_plating_receivings`;
CREATE TABLE `outsourcing_plating_receivings` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '受入ID',
  `receiving_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '受入番号',
  `receiving_date` date NOT NULL COMMENT '受入日',
  `order_id` int NOT NULL COMMENT '注文ID',
  `order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '注文番号',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `plating_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'メッキ種類',
  `order_qty` int NOT NULL COMMENT '注文数量',
  `receiving_qty` int NOT NULL COMMENT '受入数量',
  `good_qty` int NULL DEFAULT 0 COMMENT '良品数量',
  `defect_qty` int NULL DEFAULT 0 COMMENT '不良数量',
  `defect_reason` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '不良理由',
  `status` enum('pending','inspected','defect') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'pending' COMMENT '検収状態',
  `inspector` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '検収者',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `delivery_location` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '納入場所',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '区分',
  `content` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '内容',
  `specification` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `receiving_no`(`receiving_no` ASC) USING BTREE,
  INDEX `idx_receiving_no`(`receiving_no` ASC) USING BTREE,
  INDEX `idx_receiving_date`(`receiving_date` ASC) USING BTREE,
  INDEX `idx_order_id`(`order_id` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  CONSTRAINT `outsourcing_plating_receivings_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `outsourcing_plating_orders` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注メッキ受入' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_welding_orders 外注溶接注文
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_welding_orders`;
CREATE TABLE `outsourcing_welding_orders` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '注文ID',
  `order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '注文番号',
  `order_date` date NOT NULL COMMENT '注文日',
  `supplier_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `specification` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `welding_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '溶接種類',
  `welding_points` int NULL DEFAULT 0 COMMENT '溶接点数',
  `quantity` int NOT NULL COMMENT '注文数量',
  `unit` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '個' COMMENT '単位',
  `unit_price` decimal(12, 2) NULL DEFAULT 0.00 COMMENT '単価',
  `amount` decimal(14, 2) GENERATED ALWAYS AS ((`quantity` * `unit_price`)) STORED COMMENT '金額' NULL,
  `delivery_date` date NULL DEFAULT NULL COMMENT '納期',
  `delivery_location` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '納入場所',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '区分',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '内容',
  `received_qty` int NULL DEFAULT 0 COMMENT '入庫済数量',
  `status` enum('pending','ordered','partial','completed','cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'pending' COMMENT '状態',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '作成者',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `order_no`(`order_no` ASC) USING BTREE,
  INDEX `idx_order_no`(`order_no` ASC) USING BTREE,
  INDEX `idx_order_date`(`order_date` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_delivery_date`(`delivery_date` ASC) USING BTREE,
  INDEX `idx_delivery_location`(`delivery_location` ASC) USING BTREE,
  INDEX `idx_category`(`category` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注溶接注文' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_welding_stock 外注溶接品在庫
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_welding_stock`;
CREATE TABLE `outsourcing_welding_stock` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `supplier_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `welding_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '溶接種類',
  `ordered_qty` int NULL DEFAULT 0 COMMENT '発注累計数量',
  `received_qty` int NULL DEFAULT 0 COMMENT '入庫累計数量',
  `used_qty` int NULL DEFAULT 0 COMMENT '出庫累計数量',
  `stock_qty` int GENERATED ALWAYS AS ((`ordered_qty` - `used_qty`)) STORED COMMENT '現在庫数量' NULL,
  `pending_qty` int NULL DEFAULT 0 COMMENT '入庫予定数量',
  `min_stock` int NULL DEFAULT 0 COMMENT '最低在庫数',
  `last_receive_date` date NULL DEFAULT NULL COMMENT '最終入庫日',
  `last_issue_date` date NULL DEFAULT NULL COMMENT '最終出庫日',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_product_supplier_welding`(`product_cd` ASC, `supplier_cd` ASC, `welding_type` ASC) USING BTREE,
  INDEX `idx_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_welding_type`(`welding_type` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注溶接品在庫' ROW_FORMAT = Dynamic;

-- ----------------------------
-- outsourcing_welding_receivings 外注溶接受入
-- ----------------------------
DROP TABLE IF EXISTS `outsourcing_welding_receivings`;
CREATE TABLE `outsourcing_welding_receivings` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '受入ID',
  `receiving_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '受入番号',
  `receiving_date` date NOT NULL COMMENT '受入日',
  `order_id` int NOT NULL COMMENT '注文ID',
  `order_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '注文番号',
  `supplier_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '品名',
  `welding_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '溶接種類',
  `welding_points` int NULL DEFAULT 0 COMMENT '溶接点数',
  `delivery_location` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '納入場所',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '区分',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '内容',
  `specification` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `order_qty` int NOT NULL COMMENT '注文数量',
  `receiving_qty` int NOT NULL COMMENT '受入数量',
  `good_qty` int NULL DEFAULT 0 COMMENT '良品数量',
  `defect_qty` int NULL DEFAULT 0 COMMENT '不良数量',
  `defect_reason` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '不良理由',
  `status` enum('pending','inspected','defect') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'pending' COMMENT '検収状態',
  `inspector` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '検収者',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `receiving_no`(`receiving_no` ASC) USING BTREE,
  INDEX `idx_receiving_no`(`receiving_no` ASC) USING BTREE,
  INDEX `idx_receiving_date`(`receiving_date` ASC) USING BTREE,
  INDEX `idx_order_id`(`order_id` ASC) USING BTREE,
  INDEX `idx_order_no`(`order_no` ASC) USING BTREE,
  INDEX `idx_supplier_cd`(`supplier_cd` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_delivery_location`(`delivery_location` ASC) USING BTREE,
  INDEX `idx_category`(`category` ASC) USING BTREE,
  CONSTRAINT `outsourcing_welding_receivings_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `outsourcing_welding_orders` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '外注溶接受入' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Triggers: material_issue -> supplied_material_stock, material_transactions
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_material_issue_after_update`;
delimiter ;;
CREATE TRIGGER `trg_material_issue_after_update` AFTER UPDATE ON `outsourcing_material_issues` FOR EACH ROW BEGIN
    IF NEW.status = 'issued' AND OLD.status = 'preparing' THEN
        INSERT INTO outsourcing_supplied_material_stock 
        (supplier_cd, material_cd, material_name, spec, unit, unit_weight, issued_qty, last_issue_date)
        VALUES (NEW.supplier_cd, NEW.material_cd, NEW.material_name, NEW.spec, NEW.unit, NEW.unit_weight, NEW.quantity, NEW.issue_date)
        ON DUPLICATE KEY UPDATE 
            issued_qty = issued_qty + NEW.quantity,
            last_issue_date = NEW.issue_date;
        INSERT INTO outsourcing_material_transactions 
        (transaction_date, transaction_type, supplier_cd, material_cd, material_name, related_no, quantity, operator)
        VALUES (NEW.issue_date, 'issue', NEW.supplier_cd, NEW.material_cd, NEW.material_name, NEW.issue_no, NEW.quantity, NEW.operator);
    END IF;
END;;
delimiter ;

-- ----------------------------
-- Triggers: material_usage -> supplied_material_stock, material_transactions
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_material_usage_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_material_usage_after_insert` AFTER INSERT ON `outsourcing_material_usages` FOR EACH ROW BEGIN
    UPDATE outsourcing_supplied_material_stock 
    SET used_qty = used_qty + NEW.usage_qty,
        last_usage_date = NEW.usage_date
    WHERE supplier_cd = NEW.supplier_cd AND material_cd = NEW.material_cd;
    INSERT INTO outsourcing_material_transactions 
    (transaction_date, transaction_type, supplier_cd, material_cd, material_name, related_no, quantity, operator)
    VALUES (NEW.usage_date, 'usage', NEW.supplier_cd, NEW.material_cd, NEW.material_name, NEW.usage_no, NEW.usage_qty, NEW.reporter);
END;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 041_welding_orders_add_notes.sql (original prefix 041)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 041: outsourcing_welding_orders に notes 列を追加
-- 理由: 本テーブルに対する UPDATE 時に発火するトリガーが 'notes' を参照しており、
--       テーブル定義に notes が無いため 1054 Unknown column 'notes' が発生する。
--       列を追加してトリガーとの互換を取る（アプリは remarks のみ使用）。
-- 実行後、不要なトリガーは SHOW TRIGGERS WHERE `Table` = 'outsourcing_welding_orders'; で確認し削除可能。

ALTER TABLE `outsourcing_welding_orders`
  ADD COLUMN `notes` TEXT NULL COMMENT '備考(trigger互換)' AFTER `remarks`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 042_welding_order_triggers_source_file.sql (original prefix 042)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 外注溶接注文触发器：向 stock_transaction_logs 写入时增加 source_file 字段
SET NAMES utf8mb4;

-- ----------------------------
-- Trigger: trg_welding_order_after_insert
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_order_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_welding_order_after_insert` AFTER INSERT ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
    IF NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文: ', NEW.product_name, ' | 外注先: ', NEW.supplier_cd),
            NEW.unit_price,
            'outsourcing_welding_orders'
        );
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Trigger: trg_welding_order_after_update
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_welding_order_after_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_order_after_update` AFTER UPDATE ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
    IF (OLD.status <> 'ordered' OR OLD.status IS NULL) AND NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文（発注済）: ', NEW.product_name, ' | 外注先: ', NEW.supplier_cd),
            NEW.unit_price,
            'outsourcing_welding_orders'
        );
    ELSEIF NEW.status = 'ordered' AND (
        (OLD.quantity <> NEW.quantity) OR
        (OLD.unit_price <> NEW.unit_price) OR
        (OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL)) OR
        (OLD.product_cd <> NEW.product_cd)
    ) THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity - OLD.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文変更（発注済）: ', NEW.product_name,
                   IF(OLD.quantity <> NEW.quantity, CONCAT(' | 数量: ', OLD.quantity, '→', NEW.quantity), ''),
                   IF(OLD.unit_price <> NEW.unit_price, CONCAT(' | 単価: ', OLD.unit_price, '→', NEW.unit_price), ''),
                   IF(OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL), CONCAT(' | 納期変更'), ''),
                   ' | 外注先: ', NEW.supplier_cd
            ),
            NEW.unit_price,
            'outsourcing_welding_orders'
        );
    ELSEIF OLD.status = 'ordered' AND NEW.status = 'cancelled' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品',
            OLD.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            -OLD.quantity,
            OLD.unit,
            OLD.order_date,
            OLD.order_no,
            CONCAT('外注溶接注文取消: ', OLD.product_name, ' | 注文番号: ', OLD.order_no,
                   ' | 状態: ', OLD.status, '→', NEW.status, ' | 外注先: ', OLD.supplier_cd),
            OLD.unit_price,
            'outsourcing_welding_orders'
        );
    END IF;
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 043_welding_stock_log_order_no.sql (original prefix 043)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 溶接注文削除時に stock_transaction_logs を order_no で削除できるようにする
-- 1) 既存ログの order_no を notes から補完（notes 列がある場合）
-- 2) トリガーに order_no を追加し、新規挿入でも order_no を設定する

SET NAMES utf8mb4;

-- 既存データ: notes 列がある場合、source_file=outsourcing_welding_orders の order_no を notes から補完
delimiter ;;
CREATE PROCEDURE _tmp_backfill_welding_order_no()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_transaction_logs' AND COLUMN_NAME = 'notes') > 0 THEN
    UPDATE stock_transaction_logs
    SET order_no = TRIM(notes)
    WHERE source_file = 'outsourcing_welding_orders'
      AND (order_no IS NULL OR order_no = '')
      AND notes IS NOT NULL;
  END IF;
END;;
delimiter ;
CALL _tmp_backfill_welding_order_no();
DROP PROCEDURE _tmp_backfill_welding_order_no();

-- トリガー再作成: INSERT に order_no を追加（notes の代わりに order_no に注文番号を入れる）
-- 注: 042 で notes に NEW.order_no を入れているため、043 では order_no も同じ値で設定する

DROP TRIGGER IF EXISTS `trg_welding_order_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_welding_order_after_insert` AFTER INSERT ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
    IF NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            order_no,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文: ', NEW.product_name, ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_welding_orders'
        );
    END IF;
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `trg_welding_order_after_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_order_after_update` AFTER UPDATE ON `outsourcing_welding_orders` FOR EACH ROW BEGIN
    IF (OLD.status <> 'ordered' OR OLD.status IS NULL) AND NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            order_no,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文（発注済）: ', NEW.product_name, ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_welding_orders'
        );
    ELSEIF NEW.status = 'ordered' AND (
        (OLD.quantity <> NEW.quantity) OR
        (OLD.unit_price <> NEW.unit_price) OR
        (OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL)) OR
        (OLD.product_cd <> NEW.product_cd)
    ) THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            order_no,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            NEW.quantity - OLD.quantity,
            NEW.unit,
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注溶接注文変更（発注済）: ', NEW.product_name,
                   IF(OLD.quantity <> NEW.quantity, CONCAT(' | 数量: ', OLD.quantity, '→', NEW.quantity), ''),
                   IF(OLD.unit_price <> NEW.unit_price, CONCAT(' | 単価: ', OLD.unit_price, '→', NEW.unit_price), ''),
                   IF(OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL), ' | 納期変更', ''),
                   ' | 外注先: ', NEW.supplier_cd
            ),
            'outsourcing_welding_orders'
        );
    ELSEIF OLD.status = 'ordered' AND NEW.status = 'cancelled' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            order_no,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            OLD.product_cd,
            '外注倉庫',
            'KT08',
            '実績',
            -OLD.quantity,
            OLD.unit,
            OLD.order_date,
            OLD.order_no,
            CONCAT('外注溶接注文取消: ', OLD.product_name, ' | 注文番号: ', OLD.order_no,
                   ' | 状態: ', OLD.status, '→', NEW.status, ' | 外注先: ', OLD.supplier_cd),
            'outsourcing_welding_orders'
        );
    END IF;
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 044_stock_transaction_logs_add_notes.sql (original prefix 044)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- stock_transaction_logs に notes 列を追加（存在しない場合のみ）
-- 溶接注文削除時に notes = order_no のレコードも削除するため

SET NAMES utf8mb4;

delimiter ;;
CREATE PROCEDURE _tmp_add_notes_to_stock_transaction_logs()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_transaction_logs' AND COLUMN_NAME = 'notes') = 0 THEN
    ALTER TABLE stock_transaction_logs
    ADD COLUMN `notes` varchar(100) NULL DEFAULT NULL COMMENT '注文番号等（トリガー互換・削除照合用）' AFTER `order_no`;
  END IF;
END;;
delimiter ;
CALL _tmp_add_notes_to_stock_transaction_logs();
DROP PROCEDURE _tmp_add_notes_to_stock_transaction_logs;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 045_welding_receiving_trigger_source_file.sql (original prefix 045)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 外注溶接受入：任意項目変更時に stock_transaction_logs を同期（UPDATE または INSERT）、source_file を記録
-- 受入数・良品数・受入日・品名・検収者等を変更しても在庫履歴が必ず最新になる
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_welding_receiving_after_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_update` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE _remarks TEXT;

    -- 備考：受入数・良品・不良・検収者を含む（データ変更時に常に最新を反映）
    SET _remarks = CONCAT(
        '外注溶接受入: ', COALESCE(NEW.product_name, ''),
        ' | 受入番号: ', NEW.receiving_no,
        ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
        ' | 良品: ', COALESCE(NEW.good_qty, 0),
        ' | 不良: ', COALESCE(NEW.defect_qty, 0),
        ' | 外注先: ', NEW.supplier_cd,
        IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
    );

    -- 既存行があれば常に UPDATE（受入データのどの変更でも在庫履歴を同期）
    UPDATE stock_transaction_logs SET
        target_cd = NEW.product_cd,
        location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        process_cd = 'KT16' COLLATE utf8mb4_unicode_ci,
        transaction_type = '実績' COLLATE utf8mb4_unicode_ci,
        quantity = COALESCE(NEW.receiving_qty, 0),
        unit = '本' COLLATE utf8mb4_unicode_ci,
        transaction_time = CAST(NEW.receiving_date AS DATETIME),
        remarks = _remarks COLLATE utf8mb4_unicode_ci,
        unit_price = 0,
        source_file = 'outsourcing_welding_receivings'
    WHERE notes = NEW.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci;

    -- 行が無く受入数>0 のときのみ INSERT（初回受入や後から追加された受入番号用）
    IF ROW_COUNT() = 0 AND COALESCE(NEW.receiving_qty, 0) > 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            unit_price,
            source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT16' COLLATE utf8mb4_unicode_ci,
            '実績' COLLATE utf8mb4_unicode_ci,
            COALESCE(NEW.receiving_qty, 0),
            '本' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            _remarks COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_welding_receivings'
        );
    END IF;
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 046_welding_receiving_good_qty_trigger.sql (original prefix 046)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 外注溶接受入：good_qty 変更時に注文入庫数・溶接品在庫・入出庫履歴を更新（検証済み修正版）
-- 状態「受入完」: 受入数合计 >= 注文数 で判定（良品数ではなく）。入庫数(received_qty)は良品累計のまま。
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_welding_receiving_after_update_good_qty`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_update_good_qty` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE good_qty_diff INT DEFAULT 0;
    DECLARE total_received INT DEFAULT 0;   -- 该订单受入数合计（各受入记录的 receiving_qty 之和）
    DECLARE order_qty_val INT DEFAULT 0;    -- 注文数

    SET good_qty_diff = COALESCE(NEW.good_qty, 0) - COALESCE(OLD.good_qty, 0);

    IF good_qty_diff != 0 THEN
        -- 受入完判定用：该订单的受入数合计 与 注文数
        SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
        FROM outsourcing_welding_receivings WHERE order_id = NEW.order_id;
        SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = NEW.order_id LIMIT 1;

        -- 注文：入庫数=良品累計、状態=受入数合计>=注文数なら completed、否则良品>0 なら partial
        UPDATE outsourcing_welding_orders
        SET received_qty = GREATEST(0, received_qty + good_qty_diff),
            status = CASE
                WHEN total_received >= order_qty_val THEN 'completed'
                WHEN received_qty + good_qty_diff > 0 THEN 'partial'
                ELSE 'ordered'
            END
        WHERE id = NEW.order_id;

        -- 在庫テーブル：増加時は先 UPDATE、該当行がなければ INSERT（NULL welding_type でも一意扱い）
        IF good_qty_diff > 0 THEN
            UPDATE outsourcing_welding_stock
            SET received_qty = received_qty + good_qty_diff,
                last_receive_date = NEW.receiving_date
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type <=> NEW.welding_type)
            LIMIT 1;

            IF ROW_COUNT() = 0 THEN
                INSERT INTO outsourcing_welding_stock
                    (product_cd, product_name, supplier_cd, welding_type, received_qty, last_receive_date)
                VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.welding_type, good_qty_diff, NEW.receiving_date);
            END IF;
        ELSE
            -- 減少時は 1 行のみ更新（複数行マッチ時の二重減算を防止）
            UPDATE outsourcing_welding_stock
            SET received_qty = GREATEST(0, received_qty + good_qty_diff)
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type <=> NEW.welding_type)
            ORDER BY id
            LIMIT 1;
        END IF;

        -- 入庫履歴（good_qty_diff != 0 は既に外側で保証されているため IF 不要）
        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date,
            'receive',
            'welding',
            NEW.product_cd,
            NEW.product_name,
            NEW.supplier_cd,
            NEW.receiving_no,
            good_qty_diff,
            NEW.inspector
        );
    END IF;
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 047_welding_receivings_triggers_consolidated.sql (original prefix 047)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 外注溶接受入トリガー整理・修正（1ファイルに集約）
-- 表定義は 040_outsourcing_tables を参照。本ファイルはトリガーのみ DROP/CREATE。
-- 修正内容: INSERT/UPDATE の状態は「受入数合计>=注文数」で受入完、welding_stock は NULL 安全。
-- stock_transaction_logs: 1受入あたり2行（実績=良品数・不良=不良数）、任意変更で更新。DELETE 時は該当2行を削除。
SET NAMES utf8mb4;

-- =============================================================================
-- 1. AFTER INSERT：新規受入時に注文入庫数・溶接品在庫・入出庫履歴を追加
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_welding_receiving_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_insert` AFTER INSERT ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    -- 注文：入庫数に良品数を加算、状態は受入数合计>=注文数で completed
    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_welding_receivings WHERE order_id = NEW.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = NEW.order_id LIMIT 1;

    UPDATE outsourcing_welding_orders
    SET received_qty = received_qty + COALESCE(NEW.good_qty, 0),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty + COALESCE(NEW.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = NEW.order_id;

    -- 溶接品在庫：良品>0 のときのみ。先 UPDATE、該当行がなければ INSERT（NULL welding_type 対応）
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        UPDATE outsourcing_welding_stock
        SET received_qty = received_qty + NEW.good_qty,
            last_receive_date = NEW.receiving_date
        WHERE product_cd = NEW.product_cd
          AND supplier_cd = NEW.supplier_cd
          AND (welding_type <=> NEW.welding_type)
        LIMIT 1;

        IF ROW_COUNT() = 0 THEN
            INSERT INTO outsourcing_welding_stock
                (product_cd, product_name, supplier_cd, welding_type, received_qty, last_receive_date)
            VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.welding_type, NEW.good_qty, NEW.receiving_date);
        END IF;
    END IF;

    -- 入出庫履歴：良品>0 のときのみ
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date, 'receive', 'welding',
            NEW.product_cd, NEW.product_name, NEW.supplier_cd,
            NEW.receiving_no, NEW.good_qty, NEW.inspector
        );
    END IF;

    -- stock_transaction_logs：良品行（実績）・不良行（不良）を登録
    INSERT INTO stock_transaction_logs (
        stock_type, target_cd, location_cd, process_cd, transaction_type,
        quantity, unit, transaction_time, notes, remarks, unit_price, source_file
    ) VALUES (
        '仕掛品' COLLATE utf8mb4_unicode_ci,
        NEW.product_cd,
        '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        'KT16' COLLATE utf8mb4_unicode_ci,
        '実績' COLLATE utf8mb4_unicode_ci,
        COALESCE(NEW.good_qty, 0),
        '本' COLLATE utf8mb4_unicode_ci,
        CAST(NEW.receiving_date AS DATETIME),
        NEW.receiving_no,
        CONCAT(
            '外注溶接受入: ', COALESCE(NEW.product_name, ''),
            ' | 受入番号: ', NEW.receiving_no,
            ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
            ' | 良品: ', COALESCE(NEW.good_qty, 0),
            ' | 不良: ', COALESCE(NEW.defect_qty, 0),
            ' | 外注先: ', NEW.supplier_cd,
            IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
        ) COLLATE utf8mb4_unicode_ci,
        0,
        'outsourcing_welding_receivings'
    );
    INSERT INTO stock_transaction_logs (
        stock_type, target_cd, location_cd, process_cd, transaction_type,
        quantity, unit, transaction_time, notes, remarks, unit_price, source_file
    ) VALUES (
        '仕掛品' COLLATE utf8mb4_unicode_ci,
        NEW.product_cd,
        '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        'KT16' COLLATE utf8mb4_unicode_ci,
        '不良' COLLATE utf8mb4_unicode_ci,
        COALESCE(NEW.defect_qty, 0),
        '本' COLLATE utf8mb4_unicode_ci,
        CAST(NEW.receiving_date AS DATETIME),
        NEW.receiving_no,
        CONCAT(
            '外注溶接受入: ', COALESCE(NEW.product_name, ''),
            ' | 受入番号: ', NEW.receiving_no,
            ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
            ' | 良品: ', COALESCE(NEW.good_qty, 0),
            ' | 不良: ', COALESCE(NEW.defect_qty, 0),
            ' | 外注先: ', NEW.supplier_cd,
            IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
        ) COLLATE utf8mb4_unicode_ci,
        0,
        'outsourcing_welding_receivings'
    );
END
;;
delimiter ;

-- =============================================================================
-- 2. AFTER UPDATE（良品数変化）：注文入庫数・溶接品在庫・入出庫履歴を差分更新
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_welding_receiving_after_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_update` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE good_qty_diff INT DEFAULT 0;
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    SET good_qty_diff = COALESCE(NEW.good_qty, 0) - COALESCE(OLD.good_qty, 0);

    IF good_qty_diff != 0 THEN
        SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
        FROM outsourcing_welding_receivings WHERE order_id = NEW.order_id;
        SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = NEW.order_id LIMIT 1;

        UPDATE outsourcing_welding_orders
        SET received_qty = GREATEST(0, received_qty + good_qty_diff),
            status = CASE
                WHEN total_received >= order_qty_val THEN 'completed'
                WHEN received_qty + good_qty_diff > 0 THEN 'partial'
                ELSE 'ordered'
            END
        WHERE id = NEW.order_id;

        IF good_qty_diff > 0 THEN
            UPDATE outsourcing_welding_stock
            SET received_qty = received_qty + good_qty_diff,
                last_receive_date = NEW.receiving_date
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type <=> NEW.welding_type)
            LIMIT 1;
            IF ROW_COUNT() = 0 THEN
                INSERT INTO outsourcing_welding_stock
                    (product_cd, product_name, supplier_cd, welding_type, received_qty, last_receive_date)
                VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.welding_type, good_qty_diff, NEW.receiving_date);
            END IF;
        ELSE
            UPDATE outsourcing_welding_stock
            SET received_qty = GREATEST(0, received_qty + good_qty_diff)
            WHERE product_cd = NEW.product_cd
              AND supplier_cd = NEW.supplier_cd
              AND (welding_type <=> NEW.welding_type)
            ORDER BY id
            LIMIT 1;
        END IF;

        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date, 'receive', 'welding',
            NEW.product_cd, NEW.product_name, NEW.supplier_cd,
            NEW.receiving_no, good_qty_diff, NEW.inspector
        );
    END IF;
END
;;
delimiter ;

-- =============================================================================
-- 3. AFTER UPDATE（stock_transaction_logs 同期）：良品数・不良数を在庫履歴に反映（任意変更で更新）
--    実績行: quantity=良品数 / 不良行: quantity=不良数, transaction_type='不良'
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_welding_receiving_to_stock_logs_update`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_to_stock_logs_update` AFTER UPDATE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE _remarks TEXT;

    SET _remarks = CONCAT(
        '外注溶接受入: ', COALESCE(NEW.product_name, ''),
        ' | 受入番号: ', NEW.receiving_no,
        ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
        ' | 良品: ', COALESCE(NEW.good_qty, 0),
        ' | 不良: ', COALESCE(NEW.defect_qty, 0),
        ' | 外注先: ', NEW.supplier_cd,
        IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
    );

    -- 良品行（操作種別=実績、quantity=良品数）
    UPDATE stock_transaction_logs SET
        target_cd = NEW.product_cd,
        location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        process_cd = 'KT16' COLLATE utf8mb4_unicode_ci,
        transaction_type = '実績' COLLATE utf8mb4_unicode_ci,
        quantity = COALESCE(NEW.good_qty, 0),
        unit = '本' COLLATE utf8mb4_unicode_ci,
        transaction_time = CAST(NEW.receiving_date AS DATETIME),
        remarks = _remarks COLLATE utf8mb4_unicode_ci,
        unit_price = 0,
        source_file = 'outsourcing_welding_receivings'
    WHERE notes = NEW.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci
      AND transaction_type = '実績' COLLATE utf8mb4_unicode_ci;

    IF ROW_COUNT() = 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT16' COLLATE utf8mb4_unicode_ci,
            '実績' COLLATE utf8mb4_unicode_ci,
            COALESCE(NEW.good_qty, 0),
            '本' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            _remarks COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_welding_receivings'
        );
    END IF;

    -- 不良行（操作種別=不良、quantity=不良数）
    UPDATE stock_transaction_logs SET
        target_cd = NEW.product_cd,
        location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
        process_cd = 'KT16' COLLATE utf8mb4_unicode_ci,
        transaction_type = '不良' COLLATE utf8mb4_unicode_ci,
        quantity = COALESCE(NEW.defect_qty, 0),
        unit = '本' COLLATE utf8mb4_unicode_ci,
        transaction_time = CAST(NEW.receiving_date AS DATETIME),
        remarks = _remarks COLLATE utf8mb4_unicode_ci,
        unit_price = 0,
        source_file = 'outsourcing_welding_receivings'
    WHERE notes = NEW.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci
      AND transaction_type = '不良' COLLATE utf8mb4_unicode_ci;

    IF ROW_COUNT() = 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT16' COLLATE utf8mb4_unicode_ci,
            '不良' COLLATE utf8mb4_unicode_ci,
            COALESCE(NEW.defect_qty, 0),
            '本' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            _remarks COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_welding_receivings'
        );
    END IF;
END
;;
delimiter ;

-- =============================================================================
-- 4. AFTER DELETE：受入削除時に注文・在庫・履歴を回退
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_welding_receiving_after_delete`;
delimiter ;;
CREATE TRIGGER `trg_welding_receiving_after_delete` AFTER DELETE ON `outsourcing_welding_receivings` FOR EACH ROW
BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    -- 削除後残りの受入数合计（当該行は既に削除済み）
    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_welding_receivings WHERE order_id = OLD.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_welding_orders WHERE id = OLD.order_id LIMIT 1;

    UPDATE outsourcing_welding_orders
    SET received_qty = GREATEST(0, received_qty - COALESCE(OLD.good_qty, 0)),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty - COALESCE(OLD.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = OLD.order_id;

    IF COALESCE(OLD.good_qty, 0) > 0 THEN
        UPDATE outsourcing_welding_stock
        SET received_qty = GREATEST(0, received_qty - OLD.good_qty)
        WHERE product_cd = OLD.product_cd
          AND supplier_cd = OLD.supplier_cd
          AND (welding_type <=> OLD.welding_type)
        ORDER BY id
        LIMIT 1;

        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            OLD.receiving_date, 'receive', 'welding',
            OLD.product_cd, OLD.product_name, OLD.supplier_cd,
            OLD.receiving_no, -OLD.good_qty, OLD.inspector
        );
    END IF;

    -- stock_transaction_logs：当該受入の良品行・不良行を削除
    DELETE FROM stock_transaction_logs
    WHERE notes = OLD.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT16' COLLATE utf8mb4_unicode_ci
      AND source_file = 'outsourcing_welding_receivings';
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 048_stock_transaction_logs_add_defect_qty.sql (original prefix 048)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- stock_transaction_logs に defect_qty 列を追加（任意・他画面用）。
-- 成型APSの「不良」集計は transaction_type='不良' の quantity のみを使用する。
SET NAMES utf8mb4;

delimiter ;;
CREATE PROCEDURE _tmp_add_defect_qty_to_stock_transaction_logs()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'stock_transaction_logs' AND COLUMN_NAME = 'defect_qty') = 0 THEN
    ALTER TABLE stock_transaction_logs
    ADD COLUMN `defect_qty` int NULL DEFAULT NULL COMMENT '任意。成型不良集計は transaction_type=不良 の quantity を使用' AFTER `quantity`;
  END IF;
END;;
delimiter ;
CALL _tmp_add_defect_qty_to_stock_transaction_logs();
DROP PROCEDURE IF EXISTS _tmp_add_defect_qty_to_stock_transaction_logs;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 049_plating_orders_add_notes.sql (original prefix 049)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 049: outsourcing_plating_orders に notes 列を追加
-- 理由: 本テーブルに対するトリガーが stock_transaction_logs に書き込む際、
--       order_no と source_file を使用する。notes は trigger 互換用に追加（アプリは remarks のみ使用）。
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS _tmp_plating_orders_add_notes;
delimiter ;;
CREATE PROCEDURE _tmp_plating_orders_add_notes()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'outsourcing_plating_orders' AND COLUMN_NAME = 'notes') = 0 THEN
    ALTER TABLE outsourcing_plating_orders
      ADD COLUMN `notes` TEXT NULL COMMENT '備考(trigger互換)' AFTER `remarks`;
  END IF;
END;;
delimiter ;
CALL _tmp_plating_orders_add_notes();
DROP PROCEDURE IF EXISTS _tmp_plating_orders_add_notes;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 050_plating_order_triggers_source_file.sql (original prefix 050)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 外注メッキ注文触发器：向 stock_transaction_logs 写入时增加 order_no, source_file（与溶接 042/043 同逻辑）
-- process_cd: KT06 = 外注メッキ（database/api.py と一致）
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `trg_plating_order_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_plating_order_after_insert` AFTER INSERT ON `outsourcing_plating_orders` FOR EACH ROW BEGIN
    IF NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT06',
            '実績',
            NEW.quantity,
            COALESCE(NEW.unit, '本'),
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注メッキ注文: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_plating_orders'
        );
    END IF;
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `trg_plating_order_after_update`;
delimiter ;;
CREATE TRIGGER `trg_plating_order_after_update` AFTER UPDATE ON `outsourcing_plating_orders` FOR EACH ROW BEGIN
    IF (OLD.status <> 'ordered' OR OLD.status IS NULL) AND NEW.status = 'ordered' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            NEW.product_cd,
            '外注倉庫',
            'KT06',
            '実績',
            NEW.quantity,
            COALESCE(NEW.unit, '本'),
            NEW.order_date,
            NEW.order_no,
            CONCAT('外注メッキ注文（発注済）: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
            'outsourcing_plating_orders'
        );
    ELSEIF NEW.status = 'ordered' AND (
        (OLD.quantity <> NEW.quantity) OR
        (OLD.unit_price <> NEW.unit_price) OR
        (OLD.delivery_date <> NEW.delivery_date OR (OLD.delivery_date IS NULL AND NEW.delivery_date IS NOT NULL) OR (OLD.delivery_date IS NOT NULL AND NEW.delivery_date IS NULL)) OR
        (OLD.product_cd <> NEW.product_cd)
    ) THEN
        -- 直接用更新数量方式（加减しない）：既存行を quantity=NEW.quantity で更新、なければ INSERT
        -- 照合順序の混在エラー回避: notes と NEW.order_no を utf8mb4_unicode_ci で比較
        UPDATE stock_transaction_logs SET
            target_cd = NEW.product_cd,
            location_cd = '外注倉庫',
            process_cd = 'KT06',
            quantity = NEW.quantity,
            unit = COALESCE(NEW.unit, '個'),
            transaction_time = NEW.order_date,
            notes = CONVERT(NEW.order_no USING utf8mb4) COLLATE utf8mb4_unicode_ci,
            remarks = CONCAT('外注メッキ注文（発注済）: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
            source_file = 'outsourcing_plating_orders'
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.order_no COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_orders'
          AND process_cd = 'KT06'
          AND transaction_type = '実績';

        IF ROW_COUNT() = 0 THEN
            INSERT INTO stock_transaction_logs (
                stock_type,
                target_cd,
                location_cd,
                process_cd,
                transaction_type,
                quantity,
                unit,
                transaction_time,
                notes,
                remarks,
                source_file
            ) VALUES (
                '仕掛品',
                NEW.product_cd,
                '外注倉庫',
                'KT06',
                '実績',
                NEW.quantity,
                COALESCE(NEW.unit, '個'),
                NEW.order_date,
                NEW.order_no,
                CONCAT('外注メッキ注文（発注済）: ', COALESCE(NEW.product_name, ''), ' | 外注先: ', NEW.supplier_cd),
                'outsourcing_plating_orders'
            );
        END IF;
    ELSEIF OLD.status = 'ordered' AND NEW.status = 'cancelled' THEN
        INSERT INTO stock_transaction_logs (
            stock_type,
            target_cd,
            location_cd,
            process_cd,
            transaction_type,
            quantity,
            unit,
            transaction_time,
            notes,
            remarks,
            source_file
        ) VALUES (
            '仕掛品',
            OLD.product_cd,
            '外注倉庫',
            'KT06',
            '実績',
            -OLD.quantity,
            COALESCE(OLD.unit, '個'),
            OLD.order_date,
            OLD.order_no,
            CONCAT('外注メッキ注文取消: ', COALESCE(OLD.product_name, ''), ' | 注文番号: ', OLD.order_no,
                   ' | 状態: ', OLD.status, '→', NEW.status, ' | 外注先: ', OLD.supplier_cd),
            'outsourcing_plating_orders'
        );
    END IF;
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 051_plating_receivings_triggers_consolidated.sql (original prefix 051)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 外注メッキ受入トリガー（溶接 047 と同邏輯、検収状態用 process_cd=KT17・単位=個）
-- 表定義は 040_outsourcing_tables を参照。本ファイルはトリガーのみ DROP/CREATE。
-- stock_transaction_logs: 良品数・不良数が>0のときのみ該当行を保存。0のときは保存しない。DELETE 時は該当行を削除。
SET NAMES utf8mb4;

-- =============================================================================
-- 1. AFTER INSERT：新規受入時に注文入庫数・メッキ品在庫・入出庫履歴を追加
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_plating_receiving_after_insert`;
delimiter ;;
CREATE TRIGGER `trg_plating_receiving_after_insert` AFTER INSERT ON `outsourcing_plating_receivings` FOR EACH ROW
BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_plating_receivings WHERE order_id = NEW.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_plating_orders WHERE id = NEW.order_id LIMIT 1;

    UPDATE outsourcing_plating_orders
    SET received_qty = received_qty + COALESCE(NEW.good_qty, 0),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty + COALESCE(NEW.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = NEW.order_id;

    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        UPDATE outsourcing_plating_stock
        SET received_qty = received_qty + NEW.good_qty,
            last_receive_date = NEW.receiving_date
        WHERE product_cd = NEW.product_cd
          AND supplier_cd = NEW.supplier_cd
        LIMIT 1;

        IF ROW_COUNT() = 0 THEN
            INSERT INTO outsourcing_plating_stock
                (product_cd, product_name, supplier_cd, plating_type, received_qty, last_receive_date)
            VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.plating_type, NEW.good_qty, NEW.receiving_date);
        END IF;
    END IF;

    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            NEW.receiving_date, 'receive', 'plating',
            NEW.product_cd, NEW.product_name, NEW.supplier_cd,
            NEW.receiving_no, NEW.good_qty, NEW.inspector
        );
    END IF;

    -- 良品数が 0 のときは実績行を保存しない
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT17' COLLATE utf8mb4_unicode_ci,
            '実績' COLLATE utf8mb4_unicode_ci,
            NEW.good_qty,
            '個' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            CONCAT(
                '外注メッキ受入: ', COALESCE(NEW.product_name, ''),
                ' | 受入番号: ', NEW.receiving_no,
                ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
                ' | 良品: ', NEW.good_qty,
                ' | 不良: ', COALESCE(NEW.defect_qty, 0),
                ' | 外注先: ', NEW.supplier_cd,
                IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
            ) COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_plating_receivings'
        );
    END IF;
    -- 不良数が 0 のときは不良行を保存しない
    IF COALESCE(NEW.defect_qty, 0) > 0 THEN
        INSERT INTO stock_transaction_logs (
            stock_type, target_cd, location_cd, process_cd, transaction_type,
            quantity, unit, transaction_time, notes, remarks, unit_price, source_file
        ) VALUES (
            '仕掛品' COLLATE utf8mb4_unicode_ci,
            NEW.product_cd,
            '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            'KT17' COLLATE utf8mb4_unicode_ci,
            '不良' COLLATE utf8mb4_unicode_ci,
            NEW.defect_qty,
            '個' COLLATE utf8mb4_unicode_ci,
            CAST(NEW.receiving_date AS DATETIME),
            NEW.receiving_no,
            CONCAT(
                '外注メッキ受入: ', COALESCE(NEW.product_name, ''),
                ' | 受入番号: ', NEW.receiving_no,
                ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
                ' | 良品: ', COALESCE(NEW.good_qty, 0),
                ' | 不良: ', NEW.defect_qty,
                ' | 外注先: ', NEW.supplier_cd,
                IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
            ) COLLATE utf8mb4_unicode_ci,
            0,
            'outsourcing_plating_receivings'
        );
    END IF;
END
;;
delimiter ;

-- =============================================================================
-- 2. AFTER UPDATE（良品数変化）：注文入庫数・メッキ品在庫を「直接更新数量」で再計算（加减しない）
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_plating_receiving_after_update`;
delimiter ;;
CREATE TRIGGER `trg_plating_receiving_after_update` AFTER UPDATE ON `outsourcing_plating_receivings` FOR EACH ROW
BEGIN
    DECLARE total_good INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;
    DECLARE stock_received INT DEFAULT 0;

    -- 該当注文の受入良品合計で直接セット
    SELECT COALESCE(SUM(good_qty), 0) INTO total_good
    FROM outsourcing_plating_receivings WHERE order_id = NEW.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_plating_orders WHERE id = NEW.order_id LIMIT 1;

    UPDATE outsourcing_plating_orders
    SET received_qty = total_good,
        status = CASE
            WHEN total_good >= order_qty_val THEN 'completed'
            WHEN total_good > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = NEW.order_id;

    -- 該当 product_cd + supplier_cd の受入良品合計で直接セット
    SELECT COALESCE(SUM(good_qty), 0) INTO stock_received
    FROM outsourcing_plating_receivings
    WHERE product_cd = NEW.product_cd AND supplier_cd = NEW.supplier_cd;

    UPDATE outsourcing_plating_stock
    SET received_qty = stock_received,
        last_receive_date = NEW.receiving_date
    WHERE product_cd = NEW.product_cd
      AND supplier_cd = NEW.supplier_cd
    LIMIT 1;

    IF ROW_COUNT() = 0 AND stock_received > 0 THEN
        INSERT INTO outsourcing_plating_stock
            (product_cd, product_name, supplier_cd, plating_type, received_qty, last_receive_date)
        VALUES (NEW.product_cd, NEW.product_name, NEW.supplier_cd, NEW.plating_type, stock_received, NEW.receiving_date);
    END IF;

    INSERT INTO outsourcing_stock_transactions
        (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
    VALUES (
        NEW.receiving_date, 'receive', 'plating',
        NEW.product_cd, NEW.product_name, NEW.supplier_cd,
        NEW.receiving_no, COALESCE(NEW.good_qty, 0) - COALESCE(OLD.good_qty, 0), NEW.inspector
    );
END
;;
delimiter ;

-- =============================================================================
-- 3. AFTER UPDATE（stock_transaction_logs 同期）：良品数・不良数を在庫履歴に反映
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_plating_receiving_to_stock_logs_update`;
delimiter ;;
CREATE TRIGGER `trg_plating_receiving_to_stock_logs_update` AFTER UPDATE ON `outsourcing_plating_receivings` FOR EACH ROW
BEGIN
    DECLARE _remarks TEXT;

    SET _remarks = CONCAT(
        '外注メッキ受入: ', COALESCE(NEW.product_name, ''),
        ' | 受入番号: ', NEW.receiving_no,
        ' | 受入数: ', COALESCE(NEW.receiving_qty, 0),
        ' | 良品: ', COALESCE(NEW.good_qty, 0),
        ' | 不良: ', COALESCE(NEW.defect_qty, 0),
        ' | 外注先: ', NEW.supplier_cd,
        IF(NEW.inspector IS NOT NULL AND NEW.inspector != '', CONCAT(' | 検収者: ', NEW.inspector), '')
    );

    -- 良品行（実績）：良品数>0 のときのみ更新または挿入、0 のときは削除
    IF COALESCE(NEW.good_qty, 0) > 0 THEN
        UPDATE stock_transaction_logs SET
            target_cd = NEW.product_cd,
            location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            process_cd = 'KT17' COLLATE utf8mb4_unicode_ci,
            transaction_type = '実績' COLLATE utf8mb4_unicode_ci,
            quantity = NEW.good_qty,
            unit = '個' COLLATE utf8mb4_unicode_ci,
            transaction_time = CAST(NEW.receiving_date AS DATETIME),
            remarks = _remarks COLLATE utf8mb4_unicode_ci,
            unit_price = 0,
            source_file = 'outsourcing_plating_receivings'
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '実績' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';

        IF ROW_COUNT() = 0 THEN
            INSERT INTO stock_transaction_logs (
                stock_type, target_cd, location_cd, process_cd, transaction_type,
                quantity, unit, transaction_time, notes, remarks, unit_price, source_file
            ) VALUES (
                '仕掛品' COLLATE utf8mb4_unicode_ci,
                NEW.product_cd,
                '仕上倉庫' COLLATE utf8mb4_unicode_ci,
                'KT17' COLLATE utf8mb4_unicode_ci,
                '実績' COLLATE utf8mb4_unicode_ci,
                NEW.good_qty,
                '個' COLLATE utf8mb4_unicode_ci,
                CAST(NEW.receiving_date AS DATETIME),
                NEW.receiving_no,
                _remarks COLLATE utf8mb4_unicode_ci,
                0,
                'outsourcing_plating_receivings'
            );
        END IF;
    ELSE
        DELETE FROM stock_transaction_logs
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '実績' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';
    END IF;

    -- 不良行（不良）：不良数>0 のときのみ更新または挿入、0 のときは削除
    IF COALESCE(NEW.defect_qty, 0) > 0 THEN
        UPDATE stock_transaction_logs SET
            target_cd = NEW.product_cd,
            location_cd = '仕上倉庫' COLLATE utf8mb4_unicode_ci,
            process_cd = 'KT17' COLLATE utf8mb4_unicode_ci,
            transaction_type = '不良' COLLATE utf8mb4_unicode_ci,
            quantity = NEW.defect_qty,
            unit = '個' COLLATE utf8mb4_unicode_ci,
            transaction_time = CAST(NEW.receiving_date AS DATETIME),
            remarks = _remarks COLLATE utf8mb4_unicode_ci,
            unit_price = 0,
            source_file = 'outsourcing_plating_receivings'
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '不良' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';

        IF ROW_COUNT() = 0 THEN
            INSERT INTO stock_transaction_logs (
                stock_type, target_cd, location_cd, process_cd, transaction_type,
                quantity, unit, transaction_time, notes, remarks, unit_price, source_file
            ) VALUES (
                '仕掛品' COLLATE utf8mb4_unicode_ci,
                NEW.product_cd,
                '仕上倉庫' COLLATE utf8mb4_unicode_ci,
                'KT17' COLLATE utf8mb4_unicode_ci,
                '不良' COLLATE utf8mb4_unicode_ci,
                NEW.defect_qty,
                '個' COLLATE utf8mb4_unicode_ci,
                CAST(NEW.receiving_date AS DATETIME),
                NEW.receiving_no,
                _remarks COLLATE utf8mb4_unicode_ci,
                0,
                'outsourcing_plating_receivings'
            );
        END IF;
    ELSE
        DELETE FROM stock_transaction_logs
        WHERE notes COLLATE utf8mb4_unicode_ci = NEW.receiving_no COLLATE utf8mb4_unicode_ci
          AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
          AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
          AND transaction_type = '不良' COLLATE utf8mb4_unicode_ci
          AND source_file = 'outsourcing_plating_receivings';
    END IF;
END
;;
delimiter ;

-- =============================================================================
-- 4. AFTER DELETE：受入削除時に注文・在庫・履歴を回退
-- =============================================================================
DROP TRIGGER IF EXISTS `trg_plating_receiving_after_delete`;
delimiter ;;
CREATE TRIGGER `trg_plating_receiving_after_delete` AFTER DELETE ON `outsourcing_plating_receivings` FOR EACH ROW
BEGIN
    DECLARE total_received INT DEFAULT 0;
    DECLARE order_qty_val INT DEFAULT 0;

    SELECT COALESCE(SUM(receiving_qty), 0) INTO total_received
    FROM outsourcing_plating_receivings WHERE order_id = OLD.order_id;
    SELECT quantity INTO order_qty_val FROM outsourcing_plating_orders WHERE id = OLD.order_id LIMIT 1;

    UPDATE outsourcing_plating_orders
    SET received_qty = GREATEST(0, received_qty - COALESCE(OLD.good_qty, 0)),
        status = CASE
            WHEN total_received >= order_qty_val THEN 'completed'
            WHEN received_qty - COALESCE(OLD.good_qty, 0) > 0 THEN 'partial'
            ELSE 'ordered'
        END
    WHERE id = OLD.order_id;

    IF COALESCE(OLD.good_qty, 0) > 0 THEN
        UPDATE outsourcing_plating_stock
        SET received_qty = GREATEST(0, received_qty - OLD.good_qty)
        WHERE product_cd = OLD.product_cd
          AND supplier_cd = OLD.supplier_cd
        ORDER BY id
        LIMIT 1;

        INSERT INTO outsourcing_stock_transactions
            (transaction_date, transaction_type, process_type, product_cd, product_name, supplier_cd, related_no, quantity, operator)
        VALUES (
            OLD.receiving_date, 'receive', 'plating',
            OLD.product_cd, OLD.product_name, OLD.supplier_cd,
            OLD.receiving_no, -OLD.good_qty, OLD.inspector
        );
    END IF;

    DELETE FROM stock_transaction_logs
    WHERE notes = OLD.receiving_no COLLATE utf8mb4_unicode_ci
      AND stock_type = '仕掛品' COLLATE utf8mb4_unicode_ci
      AND process_cd = 'KT17' COLLATE utf8mb4_unicode_ci
      AND source_file = 'outsourcing_plating_receivings';
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 052_cutting_instruction_plans.sql (original prefix 052)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 切断指示計画テーブル（指定月でバッチ生成で production_plan_schedules から生成）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `instruction_plans`;
CREATE TABLE `instruction_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `priority_order` int NULL DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `planned_quantity` int NULL DEFAULT 0 COMMENT '計画数',
  `start_date` datetime NULL DEFAULT NULL COMMENT '開始期日',
  `end_date` datetime NULL DEFAULT NULL COMMENT '終了期日',
  `production_lot_size` int NULL DEFAULT NULL COMMENT '生産ロット数',
  `lot_number` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo.',
  `is_cutting_instructed` tinyint(1) NULL DEFAULT 0 COMMENT '切断指示（チェック）',
  `has_chamfering_process` tinyint(1) NULL DEFAULT 0 COMMENT '面取工程（チェック）',
  `is_chamfering_instructed` tinyint(1) NULL DEFAULT 0 COMMENT '面取指示（チェック）',
  `has_sw_process` tinyint(1) NULL DEFAULT 0 COMMENT 'SW工程（チェック）',
  `is_sw_instructed` tinyint(1) NULL DEFAULT 0 COMMENT 'SW指示（チェック）',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード',
  `actual_production_quantity` int NULL DEFAULT 0 COMMENT '生産数',
  `take_count` int NULL DEFAULT NULL COMMENT '取数',
  `cutting_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長',
  `chamfering_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取長',
  `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長',
  `scrap_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '端材長さ（mm）',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料',
  `material_manufacturer` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '材料メーカー',
  `standard_specification` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_production_month`(`production_month` ASC) USING BTREE,
  INDEX `idx_product_code`(`product_cd` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '切断指示計画' ROW_FORMAT = Dynamic;

DROP TRIGGER IF EXISTS `tg_generate_management_code`;
delimiter ;;
CREATE TRIGGER `tg_generate_management_code` BEFORE INSERT ON `instruction_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        NEW.product_cd,
        RIGHT(NEW.production_line, 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 053_cutting_management.sql (original prefix 053)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 切断指示テーブル（cutting_management）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `cutting_management`;
CREATE TABLE `cutting_management` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `production_order` int NULL DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int NULL DEFAULT 0 COMMENT '生産数',
  `production_time` decimal(10, 1) NULL DEFAULT NULL COMMENT '生産時間',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード',
  `production_completed_check` tinyint(1) NOT NULL DEFAULT 0 COMMENT '生産完了チェック',
  `cd` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci GENERATED ALWAYS AS (RIGHT(`management_code`, 5)) VIRTUAL COMMENT 'CD(管理コード後5位)',
  PRIMARY KEY (`id`),
  INDEX `idx_production_day` (`production_day`),
  INDEX `idx_product_cd` (`product_cd`),
  INDEX `idx_management_code` (`management_code`),
  INDEX `idx_production_month` (`production_month`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '切断指示' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 054_chamfering_management.sql (original prefix 054)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 面取指示テーブル（chamfering_management）：切断指示の次工程
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `chamfering_management`;
CREATE TABLE `chamfering_management` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `cutting_management_id` int NULL DEFAULT NULL COMMENT '元切断指示ID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `production_order` int NULL DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int NULL DEFAULT 0 COMMENT '生産数',
  `chamfering_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取長',
  `production_time` decimal(10, 1) NULL DEFAULT NULL COMMENT '生産時間',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード',
  `production_completed_check` tinyint(1) NOT NULL DEFAULT 0 COMMENT '生産完了チェック',
  `cd` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci GENERATED ALWAYS AS (RIGHT(`management_code`, 5)) VIRTUAL COMMENT 'CD(管理コード後5位)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  INDEX `idx_cutting_management_id` (`cutting_management_id`),
  INDEX `idx_production_day` (`production_day`),
  INDEX `idx_product_cd` (`product_cd`),
  INDEX `idx_management_code` (`management_code`),
  INDEX `idx_production_month` (`production_month`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '面取指示' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 055_kanban_issuance.sql (original prefix 055)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- カンバン発行テーブル（kanban_issuance）：切断・面取等の工程別カンバン発行
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `kanban_issuance`;
CREATE TABLE `kanban_issuance` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `process_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程（cutting=切断 / chamfering=面取）',
  `source_id` int NOT NULL COMMENT '元指示ID（cutting_management.id または chamfering_management.id）',
  `kanban_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'カンバン番号',
  `issue_date` date NULL DEFAULT NULL COMMENT '発行日',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'issued' COMMENT '状態（issued=発行済 / completed=完了）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  INDEX `idx_process_type` (`process_type`),
  INDEX `idx_source_id` (`source_id`),
  INDEX `idx_issue_date` (`issue_date`),
  INDEX `idx_kanban_no` (`kanban_no`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'カンバン発行' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 056_kanban_issuance_pending.sql (original prefix 056)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- カンバン発行：待発行（pending）対応（status に pending を許容、デフォルト変更）
SET NAMES utf8mb4;

ALTER TABLE `kanban_issuance`
  MODIFY COLUMN `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending'
  COMMENT '状態（pending=待発行 / issued=発行済 / completed=完了）';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 057_cutting_management_cutting_machine_display_order.sql (original prefix 057)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 切断指示：切断機（手動指定）と生産順（按切断機自動排序・可拖拽変更）
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `cutting_machine` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '切断機（手動指定）' AFTER `production_line`,
  ADD COLUMN `production_sequence` int NULL DEFAULT 0 COMMENT '生産順（同一切断機内の自動並び順、拖拽可変更）' AFTER `cutting_machine`;

UPDATE `cutting_management` SET cutting_machine = production_line WHERE cutting_machine IS NULL;
UPDATE `cutting_management` SET production_sequence = id WHERE production_sequence IS NULL OR production_sequence = 0;

ALTER TABLE `cutting_management`
  ADD INDEX `idx_cutting_machine` (`cutting_machine`),
  ADD INDEX `idx_production_sequence` (`production_sequence`);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 058_cutting_management_production_sequence.sql (original prefix 058)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 切断指示：display_order を 生産順（production_sequence）にリネーム
SET NAMES utf8mb4;

-- 既に 057 で display_order が存在する場合のみ実行（057 を未適用の場合は 057 で production_sequence が追加済みのため 058 は不要）
ALTER TABLE `cutting_management`
  DROP INDEX `idx_display_order`;
ALTER TABLE `cutting_management`
  CHANGE COLUMN `display_order` `production_sequence` int NULL DEFAULT 0 COMMENT '生産順（同一切断機内の自動並び順、拖拽可変更）';

ALTER TABLE `cutting_management`
  ADD INDEX `idx_production_sequence` (`production_sequence`);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 059_cutting_chamfering_kanban_cascade.sql (original prefix 059)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 切断→面取の参照整合性：切断指示削除時に面取指示を連動削除（API でカンバン・面取・切断の順で削除するため、本 FK は補助）
-- 運用: バッチへ戻す時は API move-from-cutting が ①カンバン ②面取 ③切断 の順で削除してから instruction_plans に挿入する
SET NAMES utf8mb4;

-- 既存の面取指示の cutting_management_id が cutting_management に存在する場合のみ FK を付与（孤立レコードがあると付与失敗）
ALTER TABLE `chamfering_management`
  ADD CONSTRAINT `fk_chamfering_cutting`
  FOREIGN KEY (`cutting_management_id`) REFERENCES `cutting_management` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 060_instruction_plans_management_code_trigger.sql (original prefix 060)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- instruction_plans の management_code トリガーを指定ロジックに統一
-- 形式: 西暦下2桁 + 月2桁 + 製品CD + ライン末尾2文字 + 順位 + - + 生産ロット数 + - + ロットNo
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_generate_management_code`;
delimiter ;;
CREATE TRIGGER `tg_generate_management_code` BEFORE INSERT ON `instruction_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        NEW.product_cd,
        RIGHT(NEW.production_line, 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 061_cutting_management_align_instruction_plans.sql (original prefix 061)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- cutting_management を instruction_plans と同じフィールド構成に揃え、production_day, cutting_machine, cd, production_completed_check を維持
SET NAMES utf8mb4;

-- 1) instruction_plans にあり cutting_management にないカラムを追加
ALTER TABLE `cutting_management`
  ADD COLUMN `priority_order` int NULL DEFAULT NULL COMMENT '順位' AFTER `production_sequence`,
  ADD COLUMN `planned_quantity` int NULL DEFAULT 0 COMMENT '計画数' AFTER `product_name`,
  ADD COLUMN `start_date` datetime NULL DEFAULT NULL COMMENT '開始期日' AFTER `planned_quantity`,
  ADD COLUMN `end_date` datetime NULL DEFAULT NULL COMMENT '終了期日' AFTER `start_date`,
  ADD COLUMN `production_lot_size` int NULL DEFAULT NULL COMMENT '生産ロット数' AFTER `end_date`,
  ADD COLUMN `lot_number` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo.' AFTER `production_lot_size`,
  ADD COLUMN `is_cutting_instructed` tinyint(1) NULL DEFAULT 0 COMMENT '切断指示' AFTER `lot_number`,
  ADD COLUMN `has_chamfering_process` tinyint(1) NULL DEFAULT 0 COMMENT '面取工程' AFTER `is_cutting_instructed`,
  ADD COLUMN `is_chamfering_instructed` tinyint(1) NULL DEFAULT 0 COMMENT '面取指示' AFTER `has_chamfering_process`,
  ADD COLUMN `has_sw_process` tinyint(1) NULL DEFAULT 0 COMMENT 'SW工程' AFTER `is_chamfering_instructed`,
  ADD COLUMN `is_sw_instructed` tinyint(1) NULL DEFAULT 0 COMMENT 'SW指示' AFTER `has_sw_process`,
  ADD COLUMN `take_count` int NULL DEFAULT NULL COMMENT '取数' AFTER `actual_production_quantity`,
  ADD COLUMN `cutting_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長' AFTER `take_count`,
  ADD COLUMN `chamfering_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取長' AFTER `cutting_length`,
  ADD COLUMN `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長' AFTER `chamfering_length`,
  ADD COLUMN `scrap_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '端材長さ(mm)' AFTER `developed_length`,
  ADD COLUMN `material_manufacturer` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '材料メーカー' AFTER `material_name`,
  ADD COLUMN `standard_specification` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格' AFTER `material_manufacturer`,
  ADD COLUMN `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時' AFTER `production_completed_check`,
  ADD COLUMN `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時' AFTER `created_at`;

-- 2) 既存データ: production_order → priority_order
UPDATE `cutting_management` SET `priority_order` = `production_order` WHERE `production_order` IS NOT NULL;

-- 3) 旧カラム削除（instruction_plans にないもの）
ALTER TABLE `cutting_management` DROP COLUMN `production_order`;
ALTER TABLE `cutting_management` DROP COLUMN `production_time`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 062_cutting_management_remarks.sql (original prefix 062)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 切断指示に備考列を追加
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '備考' AFTER `updated_at`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 063_chamfering_batch.sql (original prefix 063)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 面取バッチ一覧テーブル（chamfering_plans）：切断指示登録時に面取工程ありの場合に自動登録。面取指示へ移行前に滞留。
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `chamfering_plans`;
CREATE TABLE `chamfering_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `cutting_management_id` int NOT NULL COMMENT '元切断指示ID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `production_order` int NULL DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int NULL DEFAULT 0 COMMENT '生産数',
  `production_lot_size` int NULL DEFAULT NULL COMMENT 'ロット数',
  `lot_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo',
  `chamfering_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取長',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード',
  `cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'CD（管理コード後5位）',
  `production_completed` tinyint NULL DEFAULT NULL COMMENT '生産完了',
  `no_count` tinyint NULL DEFAULT NULL COMMENT 'カウント無',
  `has_sw_process` tinyint NULL DEFAULT NULL COMMENT 'SW工程',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  INDEX `idx_cutting_management_id` (`cutting_management_id`),
  INDEX `idx_production_month` (`production_month`),
  INDEX `idx_production_day` (`production_day`),
  INDEX `idx_production_line` (`production_line`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='面取バッチ一覧（chamfering_plans）';

-- cd フィールド：管理コード後5位をトリガーで自動設定
DROP TRIGGER IF EXISTS `chamfering_plans_cd_before_insert`;
CREATE TRIGGER `chamfering_plans_cd_before_insert`
BEFORE INSERT ON `chamfering_plans`
FOR EACH ROW
SET NEW.`cd` = IF(NEW.`management_code` IS NOT NULL AND TRIM(NEW.`management_code`) != '', RIGHT(NEW.`management_code`, 5), NULL);

DROP TRIGGER IF EXISTS `chamfering_plans_cd_before_update`;
CREATE TRIGGER `chamfering_plans_cd_before_update`
BEFORE UPDATE ON `chamfering_plans`
FOR EACH ROW
SET NEW.`cd` = IF(NEW.`management_code` IS NOT NULL AND TRIM(NEW.`management_code`) != '', RIGHT(NEW.`management_code`, 5), NULL);

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 064_chamfering_management_lot_sw.sql (original prefix 064)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 面取指示テーブルにロット数・ロットNo・SW工程を追加（面取バッチ一覧へ拖回時にデータ保持）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `chamfering_management`
  ADD COLUMN `production_lot_size` int NULL DEFAULT NULL COMMENT 'ロット数' AFTER `actual_production_quantity`,
  ADD COLUMN `lot_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo' AFTER `production_lot_size`,
  ADD COLUMN `has_sw_process` tinyint NULL DEFAULT NULL COMMENT 'SW工程' AFTER `management_code`;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 065_chamfering_management_display_fields.sql (original prefix 065)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 面取指示：表示用カラム追加（面取機、生産順、備考）
SET NAMES utf8mb4;

ALTER TABLE `chamfering_management`
  ADD COLUMN `chamfering_machine` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '面取機（手動指定）' AFTER `production_line`,
  ADD COLUMN `production_sequence` int NULL DEFAULT 0 COMMENT '生産順' AFTER `chamfering_machine`,
  ADD COLUMN `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '備考' AFTER `production_time`;

UPDATE `chamfering_management` SET chamfering_machine = production_line WHERE chamfering_machine IS NULL;
UPDATE `chamfering_management` SET production_sequence = COALESCE(production_order, id) WHERE production_sequence IS NULL OR production_sequence = 0;

ALTER TABLE `chamfering_management`
  ADD INDEX `idx_chamfering_machine` (`chamfering_machine`);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 066_chamfering_management_no_count.sql (original prefix 066)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 面取指示：カウント無（no_count）カラム追加
SET NAMES utf8mb4;

ALTER TABLE `chamfering_management`
  ADD COLUMN `no_count` tinyint NULL DEFAULT NULL COMMENT 'カウント無' AFTER `production_completed_check`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 067_kanban_issuance_rich_fields.sql (original prefix 067)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- カンバン発行：切断現品票に必要な全フィールドを kanban_issuance に追加
SET NAMES utf8mb4;

ALTER TABLE `kanban_issuance`
  ADD COLUMN `product_cd`              varchar(50)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品CD'        AFTER `status`,
  ADD COLUMN `product_name`            varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '製品名'        AFTER `product_cd`,
  ADD COLUMN `production_line`         varchar(50)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ライン'         AFTER `product_name`,
  ADD COLUMN `cutting_machine`         varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '切断機'         AFTER `production_line`,
  ADD COLUMN `material_name`           varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原材料'         AFTER `cutting_machine`,
  ADD COLUMN `standard_specification`  varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '規格'           AFTER `material_name`,
  ADD COLUMN `management_code`         varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理コード'     AFTER `standard_specification`,
  ADD COLUMN `start_date`              date         NULL DEFAULT NULL COMMENT '成型期間（開始）'                                                AFTER `management_code`,
  ADD COLUMN `end_date`                date         NULL DEFAULT NULL COMMENT '成型期間（終了）'                                                AFTER `start_date`,
  ADD COLUMN `planned_quantity`        int          NULL DEFAULT NULL COMMENT '計画数（成型計画数）'                                             AFTER `end_date`,
  ADD COLUMN `production_lot_size`     int          NULL DEFAULT NULL COMMENT '生産ロット数（成型ロット）'                                       AFTER `planned_quantity`,
  ADD COLUMN `actual_production_quantity` int       NULL DEFAULT NULL COMMENT '生産数（ロット本数）'                                             AFTER `production_lot_size`,
  ADD COLUMN `take_count`              int          NULL DEFAULT NULL COMMENT '取数'                                                            AFTER `actual_production_quantity`,
  ADD COLUMN `cutting_length`          decimal(10,2) NULL DEFAULT NULL COMMENT '切断長'                                                         AFTER `take_count`,
  ADD COLUMN `chamfering_length`       decimal(10,2) NULL DEFAULT NULL COMMENT '面取長'                                                         AFTER `cutting_length`,
  ADD COLUMN `developed_length`        decimal(10,2) NULL DEFAULT NULL COMMENT '展開長'                                                         AFTER `chamfering_length`,
  ADD COLUMN `has_chamfering_process`  tinyint(1)   NULL DEFAULT 0    COMMENT '面取工程あり'                                                    AFTER `developed_length`,
  ADD COLUMN `lot_number`              varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ロットNo.'      AFTER `has_chamfering_process`,
  ADD COLUMN `production_day`          date         NULL DEFAULT NULL COMMENT '生産日'                                                          AFTER `lot_number`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 068_instruction_plans_management_code_before_update.sql (original prefix 068)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- instruction_plans の management_code を更新時も自動再計算する BEFORE UPDATE トリガー
-- 形式: 西暦下2桁 + 月2桁 + 製品CD + ライン末尾2文字 + 順位 + - + 生産ロット数 + - + ロットNo
-- INSERT 時は既存の tg_generate_management_code (BEFORE INSERT) が実行される
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_update_management_code`;
delimiter ;;
CREATE TRIGGER `tg_update_management_code` BEFORE UPDATE ON `instruction_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 069_cutting_chamfering_defect_qty.sql (original prefix 069)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- cutting_management / chamfering_management に不良数（defect_qty）を追加
-- 不良が発生した場合の録入・管理用。実績確定時は良品数（actual_production_quantity）のみ在庫へ計上。
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `defect_qty` int NULL DEFAULT 0 COMMENT '不良数' AFTER `actual_production_quantity`;

ALTER TABLE `chamfering_management`
  ADD COLUMN `defect_qty` int NULL DEFAULT 0 COMMENT '不良数' AFTER `actual_production_quantity`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 070_chamfering_management_management_code_trigger.sql (original prefix 070)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- chamfering_management の management_code を INSERT/UPDATE 時に自動設定（instruction_plans と同形式）
-- 形式: 西暦下2桁 + 月2桁 + 製品CD + ライン末尾2文字 + 順位(production_order) + - + 生産ロット数 + - + ロットNo
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_chamfering_management_code_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_management_code_before_insert` BEFORE INSERT ON `chamfering_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.production_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `tg_chamfering_management_code_before_update`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_management_code_before_update` BEFORE UPDATE ON `chamfering_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.production_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 071_cutting_management_management_code_trigger.sql (original prefix 071)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- cutting_management の management_code を INSERT/UPDATE 時に自動設定（instruction_plans と同形式）
-- 形式: 西暦下2桁 + 月2桁 + 製品CD + ライン末尾2文字 + 順位(priority_order) + - + 生産ロット数 + - + ロットNo
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_cutting_management_code_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_cutting_management_code_before_insert` BEFORE INSERT ON `cutting_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `tg_cutting_management_code_before_update`;
delimiter ;;
CREATE TRIGGER `tg_cutting_management_code_before_update` BEFORE UPDATE ON `cutting_management` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.priority_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 072_chamfering_plans_management_code_trigger.sql (original prefix 072)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- chamfering_plans の management_code を INSERT/UPDATE 時に自動設定（instruction_plans と同形式）
-- 形式: 西暦下2桁 + 月2桁 + 製品CD + ライン末尾2文字 + 順位(production_order) + - + 生産ロット数 + - + ロットNo
-- management_code 変更時に cd（管理コード後5位）も同一トリガー内で更新するため、063 の cd 専用トリガーを削除
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `chamfering_plans_cd_before_insert`;
DROP TRIGGER IF EXISTS `chamfering_plans_cd_before_update`;

DROP TRIGGER IF EXISTS `tg_chamfering_plans_code_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_plans_code_before_insert` BEFORE INSERT ON `chamfering_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.production_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
    SET NEW.cd = IF(TRIM(COALESCE(NEW.management_code, '')) != '', RIGHT(NEW.management_code, 5), NULL);
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `tg_chamfering_plans_code_before_update`;
delimiter ;;
CREATE TRIGGER `tg_chamfering_plans_code_before_update` BEFORE UPDATE ON `chamfering_plans` FOR EACH ROW BEGIN
    SET NEW.management_code = CONCAT(
        RIGHT(YEAR(NEW.production_month), 2),
        LPAD(MONTH(NEW.production_month), 2, '0'),
        COALESCE(NEW.product_cd, ''),
        RIGHT(COALESCE(NEW.production_line, ''), 2),
        LPAD(COALESCE(NEW.production_order, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.production_lot_size, 0), 2, '0'),
        '-',
        LPAD(COALESCE(NEW.lot_number, ''), 2, '0')
    );
    SET NEW.cd = IF(TRIM(COALESCE(NEW.management_code, '')) != '', RIGHT(NEW.management_code, 5), NULL);
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 073_chamfering_plans_cutting_management_id_nullable.sql (original prefix 073)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 面取バッチ一覧（chamfering_plans）：新規追加時は cutting_management_id を NULL で登録可能にする
SET NAMES utf8mb4;

ALTER TABLE `chamfering_plans`
  MODIFY COLUMN `cutting_management_id` int NULL COMMENT '元切断指示ID（新規追加時はNULL）';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 074_material_management_tables.sql (original prefix 074)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ============================================================
-- Migration 074: 材料管理テーブル作成
-- 対象: material_inspection_master / material_logs /
--       material_stock / material_stock_sub / stock_materials
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
-- 1. 材料検品基準マスタ (material_inspection_master)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_inspection_master` (
  `id`                  int          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `inspection_cd`       varchar(50)  NOT NULL COMMENT '検験代码',
  `inspection_standard` text         NOT NULL COMMENT '検験基準',
  `created_at`          timestamp    NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at`          timestamp    NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_inspection_cd` (`inspection_cd`) COMMENT '検験代码一意'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料検品基準マスタ';

-- ------------------------------------------------------------
-- 2. 材料受入ログ (material_logs)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_logs` (
  `id`               bigint         NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `item`             varchar(100)   NOT NULL COMMENT '項目',
  `material_cd`      varchar(50)    NOT NULL COMMENT '製品CD',
  `material_name`    varchar(255)   NULL DEFAULT NULL COMMENT '製品名',
  `process_cd`       varchar(50)    NOT NULL COMMENT '工程CD',
  `log_date`         date           NOT NULL COMMENT '日付',
  `log_time`         time           NOT NULL COMMENT '時間',
  `hd_no`            varchar(50)    NULL DEFAULT NULL COMMENT 'HD番号',
  `pieces_per_bundle` int           NULL DEFAULT NULL COMMENT '1束あたりの本数',
  `quantity`         int            NULL DEFAULT NULL COMMENT '数量',
  `bundle_quantity`  int            NULL DEFAULT NULL COMMENT '束数量',
  `manufacture_no`   varchar(100)   NULL DEFAULT NULL COMMENT '製造番号',
  `manufacture_date` date           NULL DEFAULT NULL COMMENT '製造日',
  `length`           int            NULL DEFAULT NULL COMMENT '長さ(mm)',
  `outer_diameter1`  decimal(10,4)  NULL DEFAULT NULL COMMENT '外径1(mm)',
  `outer_diameter2`  decimal(10,4)  NULL DEFAULT NULL COMMENT '外径2(mm)',
  `magnetic`         varchar(1)     NULL DEFAULT NULL COMMENT '磁気',
  `appearance`       varchar(1)     NULL DEFAULT NULL COMMENT '外観',
  `supplier`         varchar(255)   NULL DEFAULT NULL COMMENT '仕入先',
  `material_quality` varchar(100)   NULL DEFAULT NULL COMMENT '材質',
  `remarks`          text           NULL COMMENT '備考',
  `note`             varchar(255)   NULL DEFAULT NULL COMMENT 'メモ',
  `created_at`       timestamp      NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at`       timestamp      NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_material_cd`  (`material_cd`),
  KEY `idx_process_cd`   (`process_cd`),
  KEY `idx_log_date`     (`log_date`),
  KEY `idx_manufacture_no` (`manufacture_no`),
  KEY `idx_supplier`     (`supplier`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料受入ログ';

-- ------------------------------------------------------------
-- 3. 材料在庫メイン (material_stock)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_stock` (
  `id`                   int           NOT NULL AUTO_INCREMENT,
  `material_cd`          varchar(50)   NOT NULL COMMENT '材料CD',
  `material_name`        varchar(50)   NOT NULL COMMENT '材料名',
  `date`                 date          NOT NULL DEFAULT '2025-01-01' COMMENT '日付',
  `initial_stock`        int           NULL DEFAULT 0  COMMENT '初期在庫',
  `current_stock`        int           NULL DEFAULT 0  COMMENT '現在在庫',
  `safety_stock`         int           NULL DEFAULT 0  COMMENT '安全在庫',
  `planned_usage`        int           NULL DEFAULT 0  COMMENT '使用数',
  `adjustment_quantity`  int           NULL DEFAULT 0  COMMENT '調整数',
  `max_stock`            int           NULL DEFAULT 0  COMMENT '最大在庫',
  `standard_spec`        varchar(50)   NULL DEFAULT '' COMMENT '規格',
  `unit`                 varchar(20)   NULL DEFAULT NULL COMMENT '単位',
  `unit_price`           decimal(15,2) NULL DEFAULT 0.00 COMMENT '単価',
  `pieces_per_bundle`    int           NULL DEFAULT 0  COMMENT '束当たり本数',
  `long_weight`          decimal(15,2) NULL DEFAULT NULL COMMENT '一本重量',
  `supplier_cd`          varchar(15)   NULL DEFAULT NULL COMMENT '仕入先CD',
  `supplier_name`        varchar(50)   NULL DEFAULT NULL COMMENT '仕入先名',
  `lead_time`            int           NULL DEFAULT 0  COMMENT 'リードタイム(日)',
  `bundle_quantity`      int           NULL DEFAULT 0  COMMENT '束本数',
  `bundle_weight`        decimal(15,2) NULL DEFAULT 0.00 COMMENT '束重量(kg)',
  `order_quantity`       int           NULL DEFAULT 0  COMMENT '注文数',
  `order_bundle_quantity` int          NULL DEFAULT 0  COMMENT '注文本数',
  `order_amount`         decimal(15,2) NULL DEFAULT 0.00 COMMENT '注文金額',
  `last_updated`         timestamp     NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最終更新日時',
  `created_at`           timestamp     NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `remarks`              varchar(50)   NULL DEFAULT '' COMMENT '備考',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_material_cd_date` (`material_cd`, `date`),
  KEY `idx_material_cd`   (`material_cd`),
  KEY `idx_supplier_cd`   (`supplier_cd`),
  KEY `idx_current_stock` (`current_stock`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料在庫メイン';

-- ------------------------------------------------------------
-- 4. 材料在庫サブ / 手動注文 (material_stock_sub)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `material_stock_sub` (
  `id`                   int           NOT NULL AUTO_INCREMENT,
  `material_cd`          varchar(50)   NOT NULL COMMENT '材料CD',
  `material_name`        varchar(255)  NOT NULL COMMENT '材料名',
  `date`                 date          NOT NULL COMMENT '日期',
  `current_stock`        decimal(10,2) NULL DEFAULT 0.00 COMMENT '現在在庫',
  `safety_stock`         decimal(10,2) NULL DEFAULT 0.00 COMMENT '安全在庫',
  `max_stock`            decimal(10,2) NULL DEFAULT 0.00 COMMENT '最大在庫',
  `unit`                 varchar(20)   NULL DEFAULT NULL COMMENT '単位',
  `unit_price`           decimal(10,2) NULL DEFAULT 0.00 COMMENT '単価',
  `supplier_cd`          varchar(50)   NULL DEFAULT NULL COMMENT '仕入先CD',
  `supplier_name`        varchar(255)  NULL DEFAULT NULL COMMENT '仕入先名',
  `lead_time`            int           NULL DEFAULT 0    COMMENT 'リードタイム',
  `planned_usage`        decimal(10,2) NULL DEFAULT 0.00 COMMENT '計画使用数',
  `order_quantity`       decimal(10,2) NULL DEFAULT 0.00 COMMENT '注文束数',
  `order_bundle_quantity` decimal(10,2) NULL DEFAULT 0.00 COMMENT '注文本数',
  `bundle_weight`        decimal(10,2) NULL DEFAULT 0.00 COMMENT '捆重量',
  `order_amount`         decimal(15,2) NULL DEFAULT 0.00 COMMENT '注文金額',
  `standard_spec`        varchar(255)  NULL DEFAULT NULL COMMENT '規格',
  `pieces_per_bundle`    int           NULL DEFAULT 0    COMMENT '每捆件数',
  `long_weight`          decimal(10,2) NULL DEFAULT 0.00 COMMENT '长重量',
  `remarks`              text          NULL COMMENT '備考',
  `created_at`           timestamp     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `last_updated`         timestamp     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最終更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_material_cd_date` (`material_cd`, `date`),
  KEY `idx_date`         (`date`),
  KEY `idx_supplier_cd`  (`supplier_cd`),
  KEY `idx_created_at`   (`created_at`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料在庫サブ（手動注文データ）';

-- ------------------------------------------------------------
-- 5. 在庫材料管理 (stock_materials)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `stock_materials` (
  `id`               int          NOT NULL AUTO_INCREMENT COMMENT '在庫材料ID',
  `material_name`    varchar(255) NOT NULL COMMENT '材料名称',
  `manufacture_no`   varchar(100) NOT NULL COMMENT '制造编号',
  `quantity`         int          NOT NULL DEFAULT 0 COMMENT '库存数量',
  `log_date`         date         NOT NULL COMMENT '日志日期',
  `supplier`         varchar(255) NULL DEFAULT NULL COMMENT '供应商',
  `material_quality` varchar(100) NULL DEFAULT NULL COMMENT '材料质量',
  `is_used`          tinyint(1)   NOT NULL DEFAULT 0 COMMENT '是否已使用(0=未使用,1=已使用)',
  `note`             varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `created_at`       timestamp    NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`       timestamp    NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_material_name`  (`material_name`),
  KEY `idx_manufacture_no` (`manufacture_no`),
  KEY `idx_log_date`       (`log_date`),
  KEY `idx_supplier`       (`supplier`),
  KEY `idx_is_used`        (`is_used`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '在庫材料管理表';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 075_material_usage_record.sql (original prefix 075)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ============================================================
-- Migration 075: 材料使用済テーブル作成
-- 切断工程の材料使用数を日次で管理し、
-- material_stock.planned_usage の更新ソースとして使用する。
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `material_usage_record` (
  `id`            int           NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `usage_date`    date          NOT NULL                COMMENT '使用日（生産日）',
  `material_cd`   varchar(50)   NOT NULL                COMMENT '材料CD（materials テーブル参照）',
  `material_name` varchar(255)  NOT NULL                COMMENT '材料名（冗長保持）',
  `usage_count`   int           NOT NULL DEFAULT 0      COMMENT '使用数（その日・その材料の不重複管理コード数）',
  `source`        varchar(50)   NOT NULL DEFAULT 'cutting' COMMENT '来源区分（cutting / chamfering など）',
  `created_at`    timestamp     NULL DEFAULT CURRENT_TIMESTAMP   COMMENT '作成日時',
  `updated_at`    timestamp     NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_usage_date_material_cd_source` (`usage_date`, `material_cd`, `source`)
    COMMENT '同一日・同一材料・同一ソースは1行（UPSERT対応）',
  KEY `idx_usage_date`  (`usage_date`),
  KEY `idx_material_cd` (`material_cd`),
  KEY `idx_source`      (`source`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT = '材料使用済テーブル（切断工程等の日次材料使用数を管理）';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 076_cutting_management_material_usage_reflected.sql (original prefix 076)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- cutting_management に使用材料の material_usage_record 反映状態を保持するカラムを追加
-- 使用数反映実行後は '反映済'、未反映は '未反映'
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `material_usage_reflected` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '未反映'
    COMMENT '使用材料が material_usage_record に反映済みか（反映済/未反映）'
    AFTER `production_completed_check`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 077_material_usage_record_management_code_reflected.sql (original prefix 077)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ============================================================
-- Migration 077: material_usage_record に管理コード・反映済を追加
-- ============================================================

SET NAMES utf8mb4;

ALTER TABLE `material_usage_record`
  ADD COLUMN `management_codes` text COMMENT '管理コード（複数はカンマ区切り）' AFTER `source`,
  ADD COLUMN `reflected` tinyint(1) NOT NULL DEFAULT 0 COMMENT '反映済（0=未反映, 1=反映済）' AFTER `management_codes`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 078_material_usage_record_single_management_code.sql (original prefix 078)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ============================================================
-- Migration 078: material_usage_record に単一管理コード列追加・ユニークキー変更
-- 旧: UNIQUE KEY (usage_date, material_cd, source)  → 集計単位での重複排除
-- 新: UNIQUE KEY (management_code, source)           → 管理コード単位での重複排除
--     management_code: cutting_management.management_code と1対1で対応（1行1件）
-- ============================================================

SET NAMES utf8mb4;

ALTER TABLE `material_usage_record`
  ADD COLUMN `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
      DEFAULT NULL
      COMMENT '管理コード（単一、cutting_management.management_code に対応）'
      AFTER `management_codes`,
  DROP KEY `uk_usage_date_material_cd_source`,
  ADD UNIQUE KEY `uk_management_code_source` (`management_code`, `source`);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 079_material_stock_add_adjustment_quantity.sql (original prefix 079)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- material_stock に adjustment_quantity が無い環境向けにカラムを追加（074 と揃える）
-- 既に存在する場合はスキップする

SET @dbname = DATABASE();
SET @tablename = 'material_stock';
SET @columnname = 'adjustment_quantity';
SET @prepared = (SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname);

SET @sql = IF(@prepared = 0,
  'ALTER TABLE `material_stock` ADD COLUMN `adjustment_quantity` int NULL DEFAULT 0 COMMENT ''調整数'' AFTER `planned_usage`',
  'SELECT 1');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 080_product_machine_config_add_sw_machine.sql (original prefix 080)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- product_machine_config に sw_machine（sw機器）カラムを追加
ALTER TABLE `product_machine_config`
  ADD COLUMN `sw_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'sw機器' AFTER `chamfering_machine`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 081_production_summarys_add_sw_machine.sql (original prefix 081)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_summarys に sw_machine（sw機器）カラムを追加（設備フィールド更新で product_machine_config.sw_machine を同期するため）
ALTER TABLE `production_summarys`
  ADD COLUMN `sw_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'sw機器' AFTER `chamfering_machine`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 082_material_stock_sub_current_stock_trigger.sql (original prefix 082)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- material_stock_sub: current_stock を order_quantity - planned_usage に応じて自動設定
-- order_quantity - planned_usage > 0 → current_stock = 1
-- order_quantity - planned_usage = 0 → current_stock = 0
SET NAMES utf8mb4;

DROP TRIGGER IF EXISTS `tg_material_stock_sub_current_stock_before_insert`;
delimiter ;;
CREATE TRIGGER `tg_material_stock_sub_current_stock_before_insert`
BEFORE INSERT ON `material_stock_sub`
FOR EACH ROW
BEGIN
  IF (COALESCE(NEW.order_quantity, 0) - COALESCE(NEW.planned_usage, 0)) > 0 THEN
    SET NEW.current_stock = 1;
  ELSE
    SET NEW.current_stock = 0;
  END IF;
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `tg_material_stock_sub_current_stock_before_update`;
delimiter ;;
CREATE TRIGGER `tg_material_stock_sub_current_stock_before_update`
BEFORE UPDATE ON `material_stock_sub`
FOR EACH ROW
BEGIN
  IF (COALESCE(NEW.order_quantity, 0) - COALESCE(NEW.planned_usage, 0)) > 0 THEN
    SET NEW.current_stock = 1;
  ELSE
    SET NEW.current_stock = 0;
  END IF;
END
;;
delimiter ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 083_material_stock_sub_label_color.sql (original prefix 083)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- material_stock_sub: ラベル色（白 / 緑）
ALTER TABLE `material_stock_sub`
  ADD COLUMN `label_color` varchar(20) NULL DEFAULT NULL COMMENT 'ラベル色（白/緑）' AFTER `remarks`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 084_instruction_plans_use_material_stock_sub_usage_count.sql (original prefix 084)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- instruction_plans: 使用サブ在庫フラグ・材料使用数（使用数反映でサブ除外・按根数集計用）
SET NAMES utf8mb4;

ALTER TABLE `instruction_plans`
  ADD COLUMN `use_material_stock_sub` tinyint(1) NOT NULL DEFAULT 0
    COMMENT '使用サブ在庫（0=反映対象, 1=対象外・material_stock_subで手動）' AFTER `standard_specification`,
  ADD COLUMN `usage_count` decimal(10,4) NOT NULL DEFAULT 1.0000
    COMMENT '材料使用数（1=1本, <1=他行と同一本を按分）' AFTER `use_material_stock_sub`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 085_cutting_management_use_material_stock_sub_usage_count.sql (original prefix 085)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- cutting_management: 使用サブ在庫フラグ・材料使用数（instruction_plans と同様）
SET NAMES utf8mb4;

ALTER TABLE `cutting_management`
  ADD COLUMN `use_material_stock_sub` tinyint(1) NOT NULL DEFAULT 0
    COMMENT '使用サブ在庫（0=反映対象, 1=対象外・material_stock_subで手動）' AFTER `material_usage_reflected`,
  ADD COLUMN `usage_count` decimal(10,4) NOT NULL DEFAULT 1.0000
    COMMENT '材料使用数（1=1本, <1=他行と同一本を按分）' AFTER `use_material_stock_sub`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 086_material_usage_record_usage_count_decimal.sql (original prefix 086)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- material_usage_record: usage_count を小数対応（按分時 0.5 等）
SET NAMES utf8mb4;

ALTER TABLE `material_usage_record`
  MODIFY COLUMN `usage_count` decimal(10,4) NOT NULL DEFAULT 1.0000
    COMMENT '使用数（行の usage_count をそのまま、按分時は <1）';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 087_production_summarys_add_sw_plan.sql (original prefix 087)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_summarys に sw_plan カラムを追加（計画データ更新で molding_actual_plan を同期するため）
ALTER TABLE `production_summarys`
  ADD COLUMN `sw_plan` int DEFAULT 0 COMMENT 'sw計画（molding_actual_planと同期）' AFTER `sw_machine`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 091_aps_schedule_tables_drop.sql (original prefix 091)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS排産スケジュール管理テーブル（回滚）

DROP TABLE IF EXISTS `aps_schedule_conflicts`;
DROP TABLE IF EXISTS `aps_schedule_blocks`;
DROP TABLE IF EXISTS `aps_schedule_runs`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 092_aps_production_scheduling_tables.sql (original prefix 092)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS 排産スケジューリング用テーブル
-- production_lines / line_capacities / production_schedules / schedule_details

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 生産ライン（設備）マスタ
CREATE TABLE IF NOT EXISTS `production_lines` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_code` VARCHAR(50) NOT NULL COMMENT '産線コード（例：加工06）',
  `default_work_hours` DECIMAL(4,2) NOT NULL DEFAULT 0.00 COMMENT '基準稼働時間（時間）',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_line_code` (`line_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生産ライン基礎情報';

-- 2. 産線日別稼働カレンダー
CREATE TABLE IF NOT EXISTS `line_capacities` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT '産線ID',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `available_hours` DECIMAL(4,2) NOT NULL COMMENT '当日可用稼働時間（時間）',
  `note` VARCHAR(255) NULL DEFAULT NULL COMMENT '備考（休日・検修等）',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_line_date` (`line_id`, `work_date`),
  INDEX `idx_work_date` (`work_date`),
  CONSTRAINT `fk_lc_line` FOREIGN KEY (`line_id`) REFERENCES `production_lines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線日別稼働カレンダー';

-- 3. 排産工単主表
CREATE TABLE IF NOT EXISTS `production_schedules` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT '産線ID',
  `order_no` INT NULL DEFAULT NULL COMMENT '順番',
  `order_id` INT NULL DEFAULT NULL COMMENT '外部注文ID',
  `item_name` VARCHAR(100) NOT NULL COMMENT '品名',
  `material_shortage` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '材料不足フラグ',
  `lot_qty` INT NOT NULL DEFAULT 0 COMMENT '実績生ロット数',
  `planned_process_qty` INT NOT NULL COMMENT '予定加工数量',
  `prev_month_carryover` INT NOT NULL DEFAULT 0 COMMENT '前月繰越',
  `due_date` DATE NULL DEFAULT NULL COMMENT '完成期日',
  `material_date` DATE NULL DEFAULT NULL COMMENT '材料調達日',
  `setup_time` INT NOT NULL DEFAULT 0 COMMENT '段取時間（分）',
  `efficiency` DECIMAL(5,2) NOT NULL DEFAULT 100.00 COMMENT '時間能率（%）',
  `daily_capacity` INT NOT NULL COMMENT '日生産能力',
  `planned_output_qty` INT NOT NULL DEFAULT 0 COMMENT '予定産出数量',
  `start_date` DATE NULL DEFAULT NULL COMMENT '開始期日',
  `end_date` DATE NULL DEFAULT NULL COMMENT '終了期日',
  `completion_rate` DECIMAL(5,2) NULL DEFAULT NULL COMMENT '完成比率（%）',
  `status` VARCHAR(20) NOT NULL DEFAULT 'PLANNING' COMMENT 'PLANNING / IN_PROGRESS / COMPLETED',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_ps_line` (`line_id`),
  INDEX `idx_ps_status` (`status`),
  CONSTRAINT `fk_ps_line` FOREIGN KEY (`line_id`) REFERENCES `production_lines` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産工単主計画表';

-- 4. 毎日排産明細（甘特図データ）
CREATE TABLE IF NOT EXISTS `schedule_details` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `schedule_id` INT NOT NULL COMMENT '工単ID',
  `schedule_date` DATE NOT NULL COMMENT '排産日',
  `planned_qty` INT NOT NULL DEFAULT 0 COMMENT '当日計画数量',
  `actual_qty` INT NOT NULL DEFAULT 0 COMMENT '実績数量',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_schedule_date` (`schedule_id`, `schedule_date`),
  INDEX `idx_sd_date` (`schedule_date`),
  CONSTRAINT `fk_sd_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='毎日排産明細/甘特図データ';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 093_line_capacity_time_slots.sql (original prefix 093)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 設備日別稼働時間帯テーブル
-- line_capacity_time_slots: 各設備の各日の稼働時間帯を管理
-- 保存時に SUM(end_time - start_time) → line_capacities.available_hours へ反映

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `line_capacity_time_slots` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT '産線ID',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `start_time` TIME NOT NULL COMMENT '開始時刻',
  `end_time` TIME NOT NULL COMMENT '終了時刻',
  `sort_order` SMALLINT NOT NULL DEFAULT 0 COMMENT '表示順',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_lcts_line_date` (`line_id`, `work_date`),
  CONSTRAINT `fk_lcts_line` FOREIGN KEY (`line_id`) REFERENCES `production_lines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備日別稼働時間帯';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 094_line_product_standard.sql (original prefix 094)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 産線×製品 標準工時マスタ
-- 製品ごとの産線における小時産能・段取時間・能率を管理

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `line_product_standard` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT '産線ID',
  `product_cd` VARCHAR(50) NOT NULL COMMENT '製品コード',
  `std_qty_per_hour` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '小時あたり標準産出量',
  `setup_time_min` INT NOT NULL DEFAULT 0 COMMENT '段取時間（分）',
  `efficiency_pct` DECIMAL(5,2) NOT NULL DEFAULT 100.00 COMMENT '標準能率（%）',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `uk_line_product` (`line_id`, `product_cd`),
  INDEX `idx_lps_product` (`product_cd`),
  CONSTRAINT `fk_lps_line` FOREIGN KEY (`line_id`) REFERENCES `production_lines` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線×製品 標準工時マスタ';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 095_production_schedules_add_product_cd.sql (original prefix 095)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_schedules に product_cd カラム追加

ALTER TABLE `production_schedules`
  ADD COLUMN `product_cd` VARCHAR(50) NULL DEFAULT NULL COMMENT '製品コード' AFTER `item_name`;

CREATE INDEX `idx_ps_product_cd` ON `production_schedules` (`product_cd`);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 096_aps_foreign_keys_to_machines.sql (original prefix 096)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS 子表の line_id を production_lines から machines へ切替
-- 先に machines に APS 用列を追加（既存ならエラーになるためそのステートメントをスキップ）

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `machines`
  ADD COLUMN `default_work_hours` DECIMAL(4,2) NULL DEFAULT NULL COMMENT '基準稼働時間（時間）' AFTER `machine_type`;

ALTER TABLE `machines`
  ADD COLUMN `is_active` TINYINT(1) NULL DEFAULT 1 COMMENT '有効フラグ' AFTER `default_work_hours`;

-- 既存 FK 削除（名前は 092/093/094 マイグレーション準拠）
ALTER TABLE `line_capacities` DROP FOREIGN KEY `fk_lc_line`;
ALTER TABLE `production_schedules` DROP FOREIGN KEY `fk_ps_line`;
ALTER TABLE `line_capacity_time_slots` DROP FOREIGN KEY `fk_lcts_line`;
ALTER TABLE `line_product_standard` DROP FOREIGN KEY `fk_lps_line`;

-- production_lines.id → machines.id（line_code = machine_cd で対応）
UPDATE `line_capacities` lc
INNER JOIN `production_lines` pl ON lc.`line_id` = pl.`id`
INNER JOIN `machines` m ON m.`machine_cd` = pl.`line_code`
SET lc.`line_id` = m.`id`;

UPDATE `production_schedules` ps
INNER JOIN `production_lines` pl ON ps.`line_id` = pl.`id`
INNER JOIN `machines` m ON m.`machine_cd` = pl.`line_code`
SET ps.`line_id` = m.`id`;

UPDATE `line_capacity_time_slots` lcts
INNER JOIN `production_lines` pl ON lcts.`line_id` = pl.`id`
INNER JOIN `machines` m ON m.`machine_cd` = pl.`line_code`
SET lcts.`line_id` = m.`id`;

UPDATE `line_product_standard` lps
INNER JOIN `production_lines` pl ON lps.`line_id` = pl.`id`
INNER JOIN `machines` m ON m.`machine_cd` = pl.`line_code`
SET lps.`line_id` = m.`id`;

-- machines に無い参照は削除（整合性のため）
DELETE lc FROM `line_capacities` lc
LEFT JOIN `machines` m ON m.`id` = lc.`line_id`
WHERE m.`id` IS NULL;

DELETE ps FROM `production_schedules` ps
LEFT JOIN `machines` m ON m.`id` = ps.`line_id`
WHERE m.`id` IS NULL;

DELETE lcts FROM `line_capacity_time_slots` lcts
LEFT JOIN `machines` m ON m.`id` = lcts.`line_id`
WHERE m.`id` IS NULL;

DELETE lps FROM `line_product_standard` lps
LEFT JOIN `machines` m ON m.`id` = lps.`line_id`
WHERE m.`id` IS NULL;

-- 新 FK（line_id は machines.id を指す意味で維持）
ALTER TABLE `line_capacities`
  ADD CONSTRAINT `fk_lc_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE;

ALTER TABLE `production_schedules`
  ADD CONSTRAINT `fk_ps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`);

ALTER TABLE `line_capacity_time_slots`
  ADD CONSTRAINT `fk_lcts_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE;

ALTER TABLE `line_product_standard`
  ADD CONSTRAINT `fk_lps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE;

SET FOREIGN_KEY_CHECKS = 1;

-- production_lines は参照されなくなったが、履歴用に残す。不要なら手動 DROP 可。
-- DROP TABLE IF EXISTS `production_lines`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 098_production_schedules_product_cd_if_missing.sql (original prefix 098)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_schedules に product_cd が無い環境向け（095 未適用時の 500 防止）
SET @dbname = DATABASE();
SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'production_schedules' AND COLUMN_NAME = 'product_cd'
);
SET @sql := IF(
  @exist = 0,
  'ALTER TABLE `production_schedules` ADD COLUMN `product_cd` VARCHAR(50) NULL DEFAULT NULL COMMENT ''製品コード'' AFTER `item_name`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'production_schedules' AND INDEX_NAME = 'idx_ps_product_cd'
);
SET @sql2 := IF(
  @idx = 0,
  'CREATE INDEX `idx_ps_product_cd` ON `production_schedules` (`product_cd`)',
  'SELECT 1'
);
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 099_schedule_slice_allocations.sql (original prefix 099)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 排産：日×時間帯ごとの計画数量（ガント時間別用）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `schedule_slice_allocations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `schedule_id` INT NOT NULL COMMENT 'production_schedules.id',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `period_start` TIME NOT NULL COMMENT '区間開始（含む）',
  `period_end` TIME NOT NULL COMMENT '区間終了（含まず）',
  `planned_qty` INT NOT NULL DEFAULT 0 COMMENT '当該区間の計画数量',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '同日並び',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ssa_sched_date` (`schedule_id`, `work_date`),
  UNIQUE KEY `uk_ssa_sched_period` (`schedule_id`, `work_date`, `period_start`, `period_end`),
  CONSTRAINT `fk_ssa_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産時間帯別配分';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 100_production_schedules_batch_fields.sql (original prefix 100)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 100: production_schedules に批次数・ロットサイズスナップショットを追加
ALTER TABLE production_schedules
  ADD COLUMN planned_batch_count INT NOT NULL DEFAULT 0,
  ADD COLUMN lot_size_snapshot   INT NOT NULL DEFAULT 0;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 101_aps_batch_plans.sql (original prefix 101)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 101: APS 批次号（バッチ）計画表
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `aps_batch_plans`;

CREATE TABLE `aps_batch_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `aps_schedule_id` int NOT NULL COMMENT 'APS production_schedules.id',
  `production_month` date NOT NULL COMMENT '生産月（YYYY-MM-01）',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン（管理コード用：下2桁が重要）',
  `priority_order` int NULL DEFAULT NULL COMMENT '順位（APS order_no）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `planned_quantity` int NOT NULL DEFAULT 0 COMMENT 'このバッチで計画する本数',
  `production_lot_size` int NOT NULL DEFAULT 0 COMMENT '総バッチ数（= lotサイズ/批次数の上限）',
  `lot_number` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ロットNo（1..N）',
  `start_date` datetime NULL DEFAULT NULL COMMENT '開始日時（時間別ガント由来）',
  `end_date` datetime NULL DEFAULT NULL COMMENT '終了日時（時間別ガント由来）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PLANNED' COMMENT '状態',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_aps_schedule_id_lot_number` (`aps_schedule_id`, `lot_number`) USING BTREE,
  INDEX `idx_aps_schedule_id` (`aps_schedule_id`),
  INDEX `idx_production_month` (`production_month`),
  INDEX `idx_product_cd` (`product_cd`)
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'APS バッチ計画' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 102_instruction_plans_add_aps_batch_plan_id.sql (original prefix 102)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 102: instruction_plans に APS バッチ参照ID を追加
SET NAMES utf8mb4;

ALTER TABLE `instruction_plans`
  ADD COLUMN `aps_batch_plan_id` int NULL DEFAULT NULL COMMENT 'APS 批次計画（aps_batch_plans.id）参照';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 103_instruction_plans_release_rollback_fields.sql (original prefix 103)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

ALTER TABLE instruction_plans
  ADD COLUMN release_cancelled_at DATETIME NULL DEFAULT NULL COMMENT '上游指示撤回日時',
  ADD COLUMN release_cancel_reason VARCHAR(255) NULL DEFAULT NULL COMMENT '上游指示撤回理由',
  ADD COLUMN release_cancel_by VARCHAR(64) NULL DEFAULT NULL COMMENT '上游指示撤回者';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 104_sync_schedule_details_actual_qty_from_stock_logs.sql (original prefix 104)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- schedule_details.actual_qty を stock_transaction_logs から同期
-- 条件: 同一日付 + 同一設備(machine_cd) + 同一製品(product_cd)
-- 対象トランザクション: transaction_type='実績'

DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ai`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_au`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ad`;

DELIMITER $$

CREATE TRIGGER `tg_stl_sync_schedule_details_ai`
AFTER INSERT ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF NEW.transaction_time IS NOT NULL
       AND NEW.machine_cd IS NOT NULL
       AND NEW.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(NEW.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_au`
AFTER UPDATE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    -- OLD キー側を再集計（移動・種別変更時の戻し）
    IF OLD.transaction_time IS NOT NULL
       AND OLD.machine_cd IS NOT NULL
       AND OLD.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(OLD.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;

    -- NEW キー側を再集計（追加/変更後）
    IF NEW.transaction_time IS NOT NULL
       AND NEW.machine_cd IS NOT NULL
       AND NEW.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(NEW.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_ad`
AFTER DELETE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF OLD.transaction_time IS NOT NULL
       AND OLD.machine_cd IS NOT NULL
       AND OLD.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(OLD.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;
END$$

DELIMITER ;

-- 既存データの一括同期
UPDATE schedule_details sd
JOIN production_schedules ps ON ps.id = sd.schedule_id
JOIN machines m ON m.id = ps.line_id
LEFT JOIN (
    SELECT
        DATE(stl.transaction_time) AS d,
        stl.machine_cd AS machine_cd,
        stl.target_cd AS product_cd,
        COALESCE(SUM(stl.quantity), 0) AS qty
    FROM stock_transaction_logs stl
    WHERE stl.transaction_type = '実績'
      AND stl.transaction_time IS NOT NULL
      AND stl.machine_cd IS NOT NULL
      AND stl.target_cd IS NOT NULL
    GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
) agg
  ON agg.d = sd.schedule_date
 AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
 AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
SET sd.actual_qty = COALESCE(agg.qty, 0);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 105_schedule_details_add_remaining_qty.sql (original prefix 105)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

ALTER TABLE schedule_details
  ADD COLUMN remaining_qty INT NOT NULL DEFAULT 0 COMMENT '差分（planned_qty - actual_qty）';

UPDATE schedule_details
SET remaining_qty = GREATEST(COALESCE(planned_qty, 0) - COALESCE(actual_qty, 0), 0);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 106_schedule_details_remaining_qty_trigger.sql (original prefix 106)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- schedule_details.remaining_qty を planned_qty / actual_qty から自動算出

DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bi`;
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bu`;

DELIMITER $$

CREATE TRIGGER `tg_schedule_details_remaining_bi`
BEFORE INSERT ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = GREATEST(COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0), 0);
END$$

CREATE TRIGGER `tg_schedule_details_remaining_bu`
BEFORE UPDATE ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = GREATEST(COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0), 0);
END$$

DELIMITER ;

-- 既存データ補正
UPDATE schedule_details
SET remaining_qty = GREATEST(COALESCE(planned_qty, 0) - COALESCE(actual_qty, 0), 0);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 200_unified_aps_schema.sql (original prefix 200)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 200: Unified APS schema baseline
-- 适用场景：新库初始化或需要一次性对齐 APS 结构的环境
-- 注意：本脚本为幂等写法；老环境仍可继续按历史迁移逐步执行

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- 1) APS core tables
-- =====================================================================

CREATE TABLE IF NOT EXISTS `line_capacities` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT 'machines.id',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `available_hours` DECIMAL(4,2) NOT NULL COMMENT '当日可用稼働時間（時間）',
  `note` VARCHAR(255) NULL DEFAULT NULL COMMENT '備考',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_line_date` (`line_id`, `work_date`),
  KEY `idx_work_date` (`work_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線日別稼働カレンダー';

CREATE TABLE IF NOT EXISTS `production_schedules` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT 'machines.id',
  `order_no` INT NULL DEFAULT NULL COMMENT '順番',
  `order_id` INT NULL DEFAULT NULL COMMENT '外部注文ID',
  `item_name` VARCHAR(100) NOT NULL COMMENT '品名',
  `product_cd` VARCHAR(50) NULL DEFAULT NULL COMMENT '製品コード',
  `material_shortage` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '材料不足フラグ',
  `lot_qty` INT NOT NULL DEFAULT 0 COMMENT '実績生ロット数',
  `planned_batch_count` INT NOT NULL DEFAULT 0 COMMENT '予定ロット数',
  `lot_size_snapshot` INT NOT NULL DEFAULT 0 COMMENT 'ロットサイズスナップショット',
  `planned_process_qty` INT NOT NULL COMMENT '予定加工数量',
  `prev_month_carryover` INT NOT NULL DEFAULT 0 COMMENT '前月繰越',
  `due_date` DATE NULL DEFAULT NULL COMMENT '完成期日',
  `material_date` DATE NULL DEFAULT NULL COMMENT '材料調達日',
  `setup_time` INT NOT NULL DEFAULT 0 COMMENT '段取時間（分）',
  `efficiency` DECIMAL(5,2) NOT NULL DEFAULT 100.00 COMMENT '時間能率（%）',
  `daily_capacity` INT NOT NULL COMMENT '日生産能力',
  `planned_output_qty` INT NOT NULL DEFAULT 0 COMMENT '予定産出数量',
  `start_date` DATE NULL DEFAULT NULL COMMENT '開始期日',
  `end_date` DATE NULL DEFAULT NULL COMMENT '終了期日',
  `completion_rate` DECIMAL(5,2) NULL DEFAULT NULL COMMENT '完成比率（%）',
  `status` VARCHAR(20) NOT NULL DEFAULT 'PLANNING' COMMENT 'PLANNING / IN_PROGRESS / COMPLETED',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ps_line` (`line_id`),
  KEY `idx_ps_status` (`status`),
  KEY `idx_ps_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産工単主計画表';

CREATE TABLE IF NOT EXISTS `schedule_details` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `schedule_id` INT NOT NULL COMMENT 'production_schedules.id',
  `schedule_date` DATE NOT NULL COMMENT '排産日',
  `planned_qty` INT NOT NULL DEFAULT 0 COMMENT '当日計画数量',
  `actual_qty` INT NOT NULL DEFAULT 0 COMMENT '実績数量',
  `remaining_qty` INT NOT NULL DEFAULT 0 COMMENT '差分（planned_qty - actual_qty）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_schedule_date` (`schedule_id`, `schedule_date`),
  KEY `idx_sd_date` (`schedule_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='毎日排産明細';

CREATE TABLE IF NOT EXISTS `line_capacity_time_slots` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT 'machines.id',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `start_time` TIME NOT NULL COMMENT '開始時刻',
  `end_time` TIME NOT NULL COMMENT '終了時刻',
  `sort_order` SMALLINT NOT NULL DEFAULT 0 COMMENT '表示順',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_lcts_line_date` (`line_id`, `work_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備日別稼働時間帯';

CREATE TABLE IF NOT EXISTS `line_product_standard` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_id` INT NOT NULL COMMENT 'machines.id',
  `product_cd` VARCHAR(50) NOT NULL COMMENT '製品コード',
  `std_qty_per_hour` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '小時あたり標準産出量',
  `setup_time_min` INT NOT NULL DEFAULT 0 COMMENT '段取時間（分）',
  `efficiency_pct` DECIMAL(5,2) NOT NULL DEFAULT 100.00 COMMENT '標準能率（%）',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_line_product` (`line_id`, `product_cd`),
  KEY `idx_lps_product` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='産線×製品標準マスタ';

CREATE TABLE IF NOT EXISTS `schedule_slice_allocations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `schedule_id` INT NOT NULL COMMENT 'production_schedules.id',
  `work_date` DATE NOT NULL COMMENT '作業日',
  `period_start` TIME NOT NULL COMMENT '区間開始（含む）',
  `period_end` TIME NOT NULL COMMENT '区間終了（含まず）',
  `planned_qty` INT NOT NULL DEFAULT 0 COMMENT '当該区間の計画数量',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '同日並び',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ssa_sched_period` (`schedule_id`, `work_date`, `period_start`, `period_end`),
  KEY `idx_ssa_sched_date` (`schedule_id`, `work_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産時間帯別配分';

CREATE TABLE IF NOT EXISTS `aps_batch_plans` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `aps_schedule_id` INT NOT NULL COMMENT 'APS production_schedules.id',
  `production_month` DATE NOT NULL COMMENT '生産月（YYYY-MM-01）',
  `production_line` VARCHAR(50) NOT NULL COMMENT 'ライン（管理コード用）',
  `priority_order` INT NULL DEFAULT NULL COMMENT '順位（APS order_no）',
  `product_cd` VARCHAR(50) NOT NULL COMMENT '製品CD',
  `product_name` VARCHAR(255) NOT NULL COMMENT '製品名',
  `planned_quantity` INT NOT NULL DEFAULT 0 COMMENT 'このバッチで計画する本数（エンジン再計算で変動しうる）',
  `original_planned_quantity` INT NULL DEFAULT NULL COMMENT '計画一覧確定時のロット本数（生産進捗の計画数表示用）',
  `production_lot_size` INT NOT NULL DEFAULT 0 COMMENT '総バッチ数',
  `lot_number` VARCHAR(100) NOT NULL COMMENT 'ロットNo',
  `start_date` DATETIME NULL DEFAULT NULL COMMENT '開始日時',
  `end_date` DATETIME NULL DEFAULT NULL COMMENT '終了日時',
  `status` VARCHAR(20) NOT NULL DEFAULT 'PLANNED' COMMENT '状態',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_aps_schedule_id_lot_number` (`aps_schedule_id`, `lot_number`),
  KEY `idx_aps_schedule_id` (`aps_schedule_id`),
  KEY `idx_production_month` (`production_month`),
  KEY `idx_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='APS バッチ計画';

-- =====================================================================
-- 2) Missing columns on existing tables (idempotent)
-- =====================================================================

SET @dbname = DATABASE();

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'instruction_plans' AND COLUMN_NAME = 'aps_batch_plan_id'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `instruction_plans` ADD COLUMN `aps_batch_plan_id` INT NULL DEFAULT NULL COMMENT ''APS 批次計画参照''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'instruction_plans' AND COLUMN_NAME = 'release_cancelled_at'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `instruction_plans` ADD COLUMN `release_cancelled_at` DATETIME NULL DEFAULT NULL COMMENT ''上游指示撤回日時''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'instruction_plans' AND COLUMN_NAME = 'release_cancel_reason'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `instruction_plans` ADD COLUMN `release_cancel_reason` VARCHAR(255) NULL DEFAULT NULL COMMENT ''上游指示撤回理由''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'instruction_plans' AND COLUMN_NAME = 'release_cancel_by'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `instruction_plans` ADD COLUMN `release_cancel_by` VARCHAR(64) NULL DEFAULT NULL COMMENT ''上游指示撤回者''',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'aps_batch_plans' AND COLUMN_NAME = 'original_planned_quantity'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `aps_batch_plans` ADD COLUMN `original_planned_quantity` INT NULL DEFAULT NULL COMMENT ''計画一覧確定時のロット本数（生産進捗の計画数表示用）'' AFTER `planned_quantity`',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE `aps_batch_plans`
SET `original_planned_quantity` = `planned_quantity`
WHERE `original_planned_quantity` IS NULL;

-- =====================================================================
-- 3) Foreign keys (drop/create safely)
-- =====================================================================

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'line_capacities' AND CONSTRAINT_NAME = 'fk_lc_machine'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `line_capacities` ADD CONSTRAINT `fk_lc_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'production_schedules' AND CONSTRAINT_NAME = 'fk_ps_machine'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `production_schedules` ADD CONSTRAINT `fk_ps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'schedule_details' AND CONSTRAINT_NAME = 'fk_sd_schedule'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `schedule_details` ADD CONSTRAINT `fk_sd_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'line_capacity_time_slots' AND CONSTRAINT_NAME = 'fk_lcts_machine'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `line_capacity_time_slots` ADD CONSTRAINT `fk_lcts_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'line_product_standard' AND CONSTRAINT_NAME = 'fk_lps_machine'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `line_product_standard` ADD CONSTRAINT `fk_lps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'schedule_slice_allocations' AND CONSTRAINT_NAME = 'fk_ssa_schedule'
);
SET @sql := IF(@fk_exists = 0,
  'ALTER TABLE `schedule_slice_allocations` ADD CONSTRAINT `fk_ssa_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `production_schedules` (`id`) ON DELETE CASCADE',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- =====================================================================
-- 4) Triggers
-- =====================================================================

DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bi`;
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bu`;

DELIMITER $$
CREATE TRIGGER `tg_schedule_details_remaining_bi`
BEFORE INSERT ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = GREATEST(COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0), 0);
END$$

CREATE TRIGGER `tg_schedule_details_remaining_bu`
BEFORE UPDATE ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = GREATEST(COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0), 0);
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ai`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_au`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ad`;

DELIMITER $$
CREATE TRIGGER `tg_stl_sync_schedule_details_ai`
AFTER INSERT ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF NEW.transaction_time IS NOT NULL
       AND NEW.machine_cd IS NOT NULL
       AND NEW.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(NEW.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_au`
AFTER UPDATE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF OLD.transaction_time IS NOT NULL
       AND OLD.machine_cd IS NOT NULL
       AND OLD.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(OLD.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;

    IF NEW.transaction_time IS NOT NULL
       AND NEW.machine_cd IS NOT NULL
       AND NEW.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(NEW.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_ad`
AFTER DELETE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF OLD.transaction_time IS NOT NULL
       AND OLD.machine_cd IS NOT NULL
       AND OLD.target_cd IS NOT NULL
    THEN
        UPDATE schedule_details sd
        JOIN production_schedules ps ON ps.id = sd.schedule_id
        JOIN machines m ON m.id = ps.line_id
        LEFT JOIN (
            SELECT
                DATE(stl.transaction_time) AS d,
                stl.machine_cd AS machine_cd,
                stl.target_cd AS product_cd,
                COALESCE(SUM(stl.quantity), 0) AS qty
            FROM stock_transaction_logs stl
            WHERE stl.transaction_type = '実績'
              AND stl.transaction_time IS NOT NULL
              AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
              AND stl.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
              AND stl.target_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci
            GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
        ) agg
          ON agg.d = sd.schedule_date
         AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
         AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
        SET sd.actual_qty = COALESCE(agg.qty, 0)
        WHERE sd.schedule_date = DATE(OLD.transaction_time)
          AND m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
          AND ps.product_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci;
    END IF;
END$$
DELIMITER ;

-- =====================================================================
-- 5) Data correction
-- =====================================================================

UPDATE schedule_details
SET remaining_qty = GREATEST(COALESCE(planned_qty, 0) - COALESCE(actual_qty, 0), 0);

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 201_aps_batch_plans_original_planned_quantity.sql (original prefix 201)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 201: ロット計画本数のスナップショット（計画一覧由来。成型実績・再排産で planned_quantity が変わっても表示用に保持）
SET NAMES utf8mb4;

SET @dbname = DATABASE();
SET @has_col := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'aps_batch_plans' AND COLUMN_NAME = 'original_planned_quantity'
);
SET @sql := IF(
  @has_col = 0,
  'ALTER TABLE `aps_batch_plans` ADD COLUMN `original_planned_quantity` INT NULL DEFAULT NULL COMMENT ''計画一覧確定時のロット本数（生産進捗の計画数表示用）'' AFTER `planned_quantity`',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE `aps_batch_plans`
SET `original_planned_quantity` = `planned_quantity`
WHERE `original_planned_quantity` IS NULL;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 202_line_capacity_time_slots_is_rest.sql (original prefix 202)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 稼働時間帯に「休憩」フラグを追加。is_rest=1 の区間は稼働合算・排産から除く。

SET NAMES utf8mb4;

ALTER TABLE `line_capacity_time_slots`
  ADD COLUMN `is_rest` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1=休憩（稼働から除く）' AFTER `sort_order`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 203_aps_menu_production_plan_parent.sql (original prefix 203)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS: 親メニュー「生産計画作成」を追加し、成型計画作成（APS_PLANNING）のみをその下に置く。
-- スケジューリング等は APS 直下（menuConfig と整合）。

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_PRODUCTION_PLAN_CREATE', '生産計画作成', m.id, NULL, 'Calendar', 1
FROM menus m WHERE m.code = 'APS' LIMIT 1;

UPDATE menus c
INNER JOIN menus p ON p.code = 'APS_PRODUCTION_PLAN_CREATE'
SET c.parent_id = p.id
WHERE c.code = 'APS_PLANNING';

UPDATE menus SET name = '成型計画作成' WHERE code = 'APS_PLANNING';

-- 成型計画メニュー権限を持つロールに親メニュー権限を付与（権限ツリー表示用）
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id AND c.code = 'APS_PLANNING'
INNER JOIN menus p ON p.code = 'APS_PRODUCTION_PLAN_CREATE';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id FROM menus WHERE code = 'APS_PRODUCTION_PLAN_CREATE';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 204_aps_four_menus_under_aps_root.sql (original prefix 204)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- スケジューリング・設備稼働設定・日別設備計画表・APSロット計画を APS 直下に戻す。
-- 「生産計画作成」配下は成型計画作成（APS_PLANNING）のみとする。

UPDATE menus c
INNER JOIN menus a ON a.code = 'APS'
SET c.parent_id = a.id
WHERE c.code IN (
  'APS_SCHEDULING', 'APS_CAPACITY', 'APS_DAILY_REPORT', 'APS_BATCH_PLANS'
);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 205_cutting_planning_tables.sql (original prefix 205)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 切断計画作成：計画Run、明細、時間帯スライス

CREATE TABLE IF NOT EXISTS `cutting_plan_runs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `production_month` date NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'DRAFT',
  `generated_at` datetime NULL DEFAULT NULL,
  `published_at` datetime NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cutting_plan_runs_month` (`production_month`),
  KEY `idx_cutting_plan_runs_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='切断計画Run';

CREATE TABLE IF NOT EXISTS `cutting_plan_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `run_id` int NOT NULL,
  `instruction_plan_id` int NULL DEFAULT NULL,
  `source_management_code` varchar(100) NULL DEFAULT NULL,
  `product_cd` varchar(50) NOT NULL,
  `product_name` varchar(255) NOT NULL,
  `material_name` varchar(255) NULL DEFAULT NULL,
  `production_line` varchar(50) NULL DEFAULT NULL,
  `planned_quantity` int NOT NULL DEFAULT 0,
  `production_lot_size` int NULL DEFAULT NULL,
  `lot_number` varchar(100) NULL DEFAULT NULL,
  `take_count` int NULL DEFAULT NULL,
  `cutting_length` decimal(10,2) NULL DEFAULT NULL,
  `assigned_machine_id` int NULL DEFAULT NULL,
  `assigned_machine` varchar(100) NULL DEFAULT NULL,
  `sequence_no` int NOT NULL DEFAULT 0,
  `planned_day` date NULL DEFAULT NULL,
  `planned_start` datetime NULL DEFAULT NULL,
  `planned_end` datetime NULL DEFAULT NULL,
  `estimated_minutes` decimal(10,2) NOT NULL DEFAULT 0,
  `efficiency_rate` decimal(10,2) NULL DEFAULT NULL,
  `setup_time_min` int NULL DEFAULT NULL,
  `is_locked` tinyint(1) NOT NULL DEFAULT 0,
  `publish_status` varchar(20) NOT NULL DEFAULT 'PLANNED',
  `published_cutting_id` int NULL DEFAULT NULL,
  `actual_quantity` int NOT NULL DEFAULT 0,
  `completion_status` varchar(20) NOT NULL DEFAULT 'PLANNED',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_cutting_plan_items_run` (`run_id`),
  KEY `idx_cutting_plan_items_machine_seq` (`run_id`, `assigned_machine_id`, `sequence_no`),
  KEY `idx_cutting_plan_items_day` (`run_id`, `planned_day`),
  KEY `idx_cutting_plan_items_instruction` (`instruction_plan_id`),
  KEY `idx_cutting_plan_items_management_code` (`source_management_code`),
  KEY `idx_cutting_plan_items_published_cutting` (`published_cutting_id`),
  CONSTRAINT `fk_cutting_plan_items_run` FOREIGN KEY (`run_id`) REFERENCES `cutting_plan_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='切断計画明細';

CREATE TABLE IF NOT EXISTS `cutting_plan_slices` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `run_id` int NOT NULL,
  `item_id` bigint NOT NULL,
  `machine_id` int NULL DEFAULT NULL,
  `assigned_machine` varchar(100) NULL DEFAULT NULL,
  `work_date` date NOT NULL,
  `period_start` time NOT NULL,
  `period_end` time NOT NULL,
  `planned_qty` int NOT NULL DEFAULT 0,
  `sort_order` int NOT NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_cutting_plan_slices_run_day` (`run_id`, `work_date`),
  KEY `idx_cutting_plan_slices_item` (`item_id`),
  KEY `idx_cutting_plan_slices_machine` (`machine_id`, `work_date`),
  CONSTRAINT `fk_cutting_plan_slices_run` FOREIGN KEY (`run_id`) REFERENCES `cutting_plan_runs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cutting_plan_slices_item` FOREIGN KEY (`item_id`) REFERENCES `cutting_plan_items` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='切断計画時間帯スライス';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 206_aps_cutting_planning_menu.sql (original prefix 206)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS: 生産計画作成 配下に「切断計画作成」を追加

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_CUTTING_PLANNING', '切断計画作成', m.id, '/aps/cutting-planning', 'Operation', 2
FROM menus m
WHERE m.code = 'APS_PRODUCTION_PLAN_CREATE'
LIMIT 1;

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'APS_PRODUCTION_PLAN_CREATE'
INNER JOIN menus child ON child.code = 'APS_CUTTING_PLANNING';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_CUTTING_PLANNING';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 207_cutting_plan_items_instruction_production_qty.sql (original prefix 207)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- cutting_plan_items: 指示計画の生産数（instruction_plans.actual_production_quantity）を保持し一覧表示用にする

ALTER TABLE `cutting_plan_items`
  ADD COLUMN `instruction_production_quantity` int NOT NULL DEFAULT 0 COMMENT '指示計画の生産数' AFTER `planned_quantity`;

UPDATE `cutting_plan_items` cpi
INNER JOIN `instruction_plans` ip ON cpi.instruction_plan_id = ip.id
SET cpi.instruction_production_quantity = COALESCE(ip.actual_production_quantity, 0)
WHERE cpi.instruction_plan_id IS NOT NULL;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 208_chamfering_plans_management_length_fields.sql (original prefix 208)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- chamfering_plans / chamfering_management に instruction_plans と同様の切断長・展開長を追加（製品マスタ同期用）
SET NAMES utf8mb4;

ALTER TABLE `chamfering_plans`
  ADD COLUMN `cutting_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長' AFTER `lot_number`,
  ADD COLUMN `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長' AFTER `chamfering_length`;

ALTER TABLE `chamfering_management`
  ADD COLUMN `cutting_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長' AFTER `lot_number`,
  ADD COLUMN `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長' AFTER `chamfering_length`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 209_product_bom_tables.sql (original prefix 209)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 明細BOM（product_bom_headers / product_bom_lines）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_bom_headers` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `parent_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '親製品CD',
  `bom_type` varchar(30) NOT NULL DEFAULT 'production' COMMENT 'BOM種別 (engineering/production)',
  `revision` varchar(20) NOT NULL DEFAULT '1' COMMENT '版番',
  `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '状態 (active/historical)',
  `effective_from` date DEFAULT NULL COMMENT '有効開始日',
  `effective_to` date DEFAULT NULL COMMENT '有効終了日 (NULL=無期限)',
  `base_quantity` decimal(12,4) NOT NULL DEFAULT 1.0000 COMMENT '基準数量',
  `uom` varchar(20) NOT NULL DEFAULT '個' COMMENT '単位',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_bom_hdr_parent` (`parent_product_cd`),
  KEY `idx_bom_hdr_effective` (`parent_product_cd`, `bom_type`, `effective_from`, `effective_to`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='明細BOMヘッダ';

CREATE TABLE IF NOT EXISTS `product_bom_lines` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `header_id` int NOT NULL COMMENT 'ヘッダID',
  `parent_line_id` int DEFAULT NULL COMMENT '親行ID (多階層)',
  `line_no` int NOT NULL DEFAULT 10 COMMENT '行番号',
  `component_type` varchar(30) NOT NULL DEFAULT 'material' COMMENT '子品目種別 (material/purchased/subassy/phantom)',
  `component_product_cd` varchar(50) DEFAULT NULL COMMENT '子品目の製品CD',
  `component_material_cd` varchar(50) DEFAULT NULL COMMENT '子品目の材料CD',
  `qty_per` decimal(12,6) NOT NULL DEFAULT 1.000000 COMMENT '親1基準あたり所要量',
  `uom` varchar(20) NOT NULL DEFAULT '個' COMMENT '単位',
  `scrap_rate` decimal(5,2) DEFAULT 0.00 COMMENT 'スクラップ率 (%)',
  `consume_process_cd` varchar(50) DEFAULT NULL COMMENT '投入工程CD',
  `consume_step_no` int DEFAULT NULL COMMENT '投入ステップ番号',
  `remarks` text COMMENT '備考',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_bom_line_header` (`header_id`),
  KEY `idx_bom_line_parent_line` (`parent_line_id`),
  KEY `idx_bom_line_component` (`component_product_cd`),
  CONSTRAINT `fk_bom_line_header` FOREIGN KEY (`header_id`) REFERENCES `product_bom_headers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_bom_line_parent` FOREIGN KEY (`parent_line_id`) REFERENCES `product_bom_lines` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='明細BOM行';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 210_product_process_unit_prices.sql (original prefix 210)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 工程別標準原価増分テーブル
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `product_process_unit_prices` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品CD',
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートCD',
  `step_no` int NOT NULL COMMENT 'ステップ番号',
  `line_seq` int NOT NULL DEFAULT 1 COMMENT '行連番 (同ステップ内)',
  `line_type` varchar(30) NOT NULL DEFAULT 'process' COMMENT '種別 (material/process/other)',
  `description` varchar(200) DEFAULT NULL COMMENT '内容説明',
  `increment_unit_price` decimal(18,6) NOT NULL DEFAULT 0.000000 COMMENT '増分単価',
  `currency` varchar(10) NOT NULL DEFAULT 'JPY' COMMENT '通貨',
  `effective_from` date DEFAULT NULL COMMENT '有効開始日',
  `effective_to` date DEFAULT NULL COMMENT '有効終了日 (NULL=無期限)',
  `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '状態',
  `bom_line_id` int DEFAULT NULL COMMENT '参照BOM行ID (追跡用)',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_price_product_route` (`product_cd`, `route_cd`),
  KEY `idx_price_effective` (`product_cd`, `route_cd`, `effective_from`, `effective_to`),
  KEY `idx_price_step` (`product_cd`, `route_cd`, `step_no`, `line_seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工程別標準原価増分';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 211_inventory_value_calc_tables.sql (original prefix 211)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 棚卸金額計算バッチ・明細スナップショット
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `inventory_value_calc_runs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `calc_date` date NOT NULL COMMENT '計算対象日',
  `start_date` date DEFAULT NULL COMMENT '対象期間開始',
  `end_date` date DEFAULT NULL COMMENT '対象期間終了',
  `process_cd` varchar(50) DEFAULT NULL COMMENT '絞込工程 (NULL=全)',
  `total_amount` decimal(18,2) NOT NULL DEFAULT 0.00,
  `material_amount` decimal(18,2) NOT NULL DEFAULT 0.00,
  `component_amount` decimal(18,2) NOT NULL DEFAULT 0.00,
  `stay_amount` decimal(18,2) NOT NULL DEFAULT 0.00,
  `total_rows` int NOT NULL DEFAULT 0,
  `error_rows` int NOT NULL DEFAULT 0,
  `status` varchar(20) NOT NULL DEFAULT 'completed' COMMENT '状態 (running/completed/failed)',
  `executed_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_calc_run_date` (`calc_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='棚卸金額計算バッチ';

CREATE TABLE IF NOT EXISTS `inventory_value_calc_details` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `run_id` int NOT NULL COMMENT '計算バッチID',
  `inventory_log_id` int DEFAULT NULL COMMENT '棚卸ログID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `item_type` varchar(30) DEFAULT NULL COMMENT '区分 (材料/部品/ステー)',
  `quantity` decimal(12,4) DEFAULT 0.0000,
  `route_cd` varchar(50) DEFAULT NULL COMMENT '適用ルートCD',
  `step_no` int DEFAULT NULL COMMENT '適用ステップ',
  `unit_price_snapshot` decimal(18,6) DEFAULT NULL COMMENT 'スナップショット累計単価',
  `amount` decimal(18,2) DEFAULT NULL COMMENT '金額 (数量×単価)',
  `price_rule_id` int DEFAULT NULL COMMENT '適用単価ルールID',
  `error_code` varchar(50) DEFAULT NULL COMMENT 'エラーコード (NULL=正常)',
  `error_message` varchar(500) DEFAULT NULL COMMENT 'エラー内容',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_calc_detail_run` (`run_id`),
  KEY `idx_calc_detail_product` (`product_cd`, `process_cd`),
  CONSTRAINT `fk_calc_detail_run` FOREIGN KEY (`run_id`) REFERENCES `inventory_value_calc_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='棚卸金額計算明細';

SET FOREIGN_KEY_CHECKS = 1;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 212_material_cutting_logs.sql (original prefix 212)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- material_cutting_logs: materialCutting.csv の手動インポート先
CREATE TABLE IF NOT EXISTS material_cutting_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    item            VARCHAR(100),
    log_date        DATE,
    log_time        TIME,
    hd_no           VARCHAR(255),
    operator_name   VARCHAR(100),
    material_cd     VARCHAR(255),
    management_code VARCHAR(255),
    raw_line        TEXT,
    source_file     VARCHAR(500),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mcl_log_date (log_date),
    INDEX idx_mcl_hd_no (hd_no),
    INDEX idx_mcl_material_cd (material_cd),
    INDEX idx_mcl_management_code (management_code)
);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 213_material_cutting_logs_manufacture_no.sql (original prefix 213)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- material_cutting_logs: manufacture_no（材料コードからトリガーで自動設定）
-- ルール:
--   1) material_cd に「荒井」を含む → 'A' + material_cd の先頭13文字
--   2) material_cd が N で始まる（先頭空白除く）→ material_cd の先頭8文字
--   3) それ以外 → material_cd 全文
SET NAMES utf8mb4;

ALTER TABLE `material_cutting_logs`
    ADD COLUMN `manufacture_no` VARCHAR(255) NULL DEFAULT NULL COMMENT '製造番号（材料コードより自動算出）' AFTER `material_cd`;

DROP TRIGGER IF EXISTS `tg_material_cutting_logs_manufacture_no_bi`;
delimiter ;;
CREATE TRIGGER `tg_material_cutting_logs_manufacture_no_bi` BEFORE INSERT ON `material_cutting_logs` FOR EACH ROW
BEGIN
    IF NEW.material_cd IS NULL OR TRIM(NEW.material_cd) = '' THEN
        SET NEW.manufacture_no = NULL;
    ELSEIF NEW.material_cd LIKE '%荒井%' THEN
        SET NEW.manufacture_no = CONCAT('A', LEFT(NEW.material_cd, 13));
    ELSEIF LEFT(LTRIM(NEW.material_cd), 1) = 'N' THEN
        SET NEW.manufacture_no = LEFT(NEW.material_cd, 8);
    ELSE
        SET NEW.manufacture_no = NEW.material_cd;
    END IF;
END
;;
delimiter ;

DROP TRIGGER IF EXISTS `tg_material_cutting_logs_manufacture_no_bu`;
delimiter ;;
CREATE TRIGGER `tg_material_cutting_logs_manufacture_no_bu` BEFORE UPDATE ON `material_cutting_logs` FOR EACH ROW
BEGIN
    IF NEW.material_cd IS NULL OR TRIM(NEW.material_cd) = '' THEN
        SET NEW.manufacture_no = NULL;
    ELSEIF NEW.material_cd LIKE '%荒井%' THEN
        SET NEW.manufacture_no = CONCAT('A', LEFT(NEW.material_cd, 13));
    ELSEIF LEFT(LTRIM(NEW.material_cd), 1) = 'N' THEN
        SET NEW.manufacture_no = LEFT(NEW.material_cd, 8);
    ELSE
        SET NEW.manufacture_no = NEW.material_cd;
    END IF;
END
;;
delimiter ;

-- 既存行のバックフィル
UPDATE `material_cutting_logs`
SET `manufacture_no` = CASE
    WHEN `material_cd` IS NULL OR TRIM(`material_cd`) = '' THEN NULL
    WHEN `material_cd` LIKE '%荒井%' THEN CONCAT('A', LEFT(`material_cd`, 13))
    WHEN LEFT(LTRIM(`material_cd`), 1) = 'N' THEN LEFT(`material_cd`, 8)
    ELSE `material_cd`
END;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 214_process_processing_fees.sql (original prefix 214)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 工程加工費マスタ（工程＋加工方法ごとに加工費）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `process_processing_fees` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '工程CD（processes.process_cd）',
  `method_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '加工方法コード',
  `method_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '加工方法名称',
  `unit_price` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '加工費単価',
  `currency` varchar(10) NOT NULL DEFAULT 'JPY' COMMENT '通貨',
  `charge_uom` varchar(20) NOT NULL DEFAULT '式' COMMENT '課金単位（式/個/H 等）',
  `effective_from` date DEFAULT NULL COMMENT '有効開始',
  `effective_to` date DEFAULT NULL COMMENT '有効終了',
  `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '状態 active/historical',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ppf_process` (`process_cd`),
  KEY `idx_ppf_process_method` (`process_cd`, `method_cd`),
  KEY `idx_ppf_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='工程加工費マスタ';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 215_part_masters.sql (original prefix 215)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 部品マスタ（外購部品・子assemblyの標準単価・通貨・為替）— テーブル名 parts
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `parts` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `part_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '部品CD（BOMの子品目CDと同一可）',
  `part_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '部品名',
  `category` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '分类',
  `kind` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'N' COMMENT '種別 T/N/F',
  `settlement_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '有償支給' COMMENT '決済種類',
  `uom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '個' COMMENT '単位',
  `unit_price` decimal(18,6) NOT NULL DEFAULT 0.000000 COMMENT '単価（原通貨）',
  `material_unit_price` decimal(18,6) NOT NULL DEFAULT 0.000000 COMMENT '部品材料単価（原通貨）',
  `total_unit_price` decimal(18,6) GENERATED ALWAYS AS (`unit_price` + `material_unit_price`) STORED COMMENT '総単価（単価+部品材料単価）',
  `currency` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'JPY' COMMENT '通貨コード',
  `exchange_rate` decimal(18,6) NOT NULL DEFAULT 1.000000 COMMENT '基準通貨JPY換算：1原通貨当たり円（JPY時は1）',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '主仕入先CD',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '1=有効 0=無効',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_parts_part_cd` (`part_cd`),
  KEY `idx_parts_status` (`status`),
  KEY `idx_parts_kind` (`kind`),
  KEY `idx_parts_settlement_type` (`settlement_type`),
  CONSTRAINT `chk_parts_kind` CHECK (`kind` IN ('T','N','F')),
  CONSTRAINT `chk_parts_settlement_type` CHECK (`settlement_type` IN ('有償支給','無償支給','自給','その他'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='部品マスタ';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 216_parts_settlement_type.sql (original prefix 216)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 既存の parts テーブルに決済種類を追加（215 を「settlement_type 追加前」の内容で既に適用済みの DB 向け）
-- 新規環境で 215（settlement_type 入り）を適用済みの場合は実行しないでください（重複カラムエラーになります）。
SET NAMES utf8mb4;

ALTER TABLE `parts`
  ADD COLUMN `settlement_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '有償支給' COMMENT '決済種類' AFTER `kind`,
  ADD KEY `idx_parts_settlement_type` (`settlement_type`),
  ADD CONSTRAINT `chk_parts_settlement_type` CHECK (`settlement_type` IN ('有償支給','無償支給','自給','その他'));

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 217_aps_forming_plan_list_menu.sql (original prefix 217)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS：生産計画作成配下に「成型計画一覧」を追加（/aps/planning-list）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_FORMING_PLAN_LIST', '成型計画一覧', m.id, '/aps/planning-list', 'List', 3
FROM menus m
WHERE m.code = 'APS_PRODUCTION_PLAN_CREATE'
LIMIT 1;

-- 成型計画作成と同じロールに一覧メニューを付与
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'APS_PLANNING'
INNER JOIN menus child ON child.code = 'APS_FORMING_PLAN_LIST';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_FORMING_PLAN_LIST';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 218_aps_production_plan_view_parent_menu.sql (original prefix 218)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS：親メニュー「生産計画一覧」を APS 直下に追加し、「成型計画一覧」をその配下へ移す（menuConfig / Sidebar 整合）

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_PRODUCTION_PLAN_VIEW', '生産計画一覧', m.id, NULL, 'List', 1.5
FROM menus m
WHERE m.code = 'APS'
LIMIT 1;

UPDATE menus child
INNER JOIN menus new_parent ON new_parent.code = 'APS_PRODUCTION_PLAN_VIEW'
SET child.parent_id = new_parent.id, child.sort_order = 1
WHERE child.code = 'APS_FORMING_PLAN_LIST';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, p.id
FROM role_menu_permissions rmp
INNER JOIN menus c ON c.id = rmp.menu_id AND c.code = 'APS_FORMING_PLAN_LIST'
INNER JOIN menus p ON p.code = 'APS_PRODUCTION_PLAN_VIEW';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_PRODUCTION_PLAN_VIEW';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 219_ensure_erp_inventory_tables.sql (original prefix 219)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 在庫関連コアテーブル（003 と同等・IF NOT EXISTS で未作成環境向け）
-- 既に 003 を適用済みの DB では何も変わりません。

CREATE TABLE IF NOT EXISTS warehouse (
    id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_code VARCHAR(50) NOT NULL UNIQUE,
    warehouse_name VARCHAR(200) NOT NULL,
    warehouse_type VARCHAR(30) DEFAULT 'product' COMMENT 'material,product,semi_finished,defective,transit',
    address VARCHAR(500),
    manager VARCHAR(100),
    phone VARCHAR(20),
    capacity INT,
    is_active BOOLEAN DEFAULT TRUE,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_warehouse_code (warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    warehouse_code VARCHAR(50) NOT NULL,
    warehouse_name VARCHAR(200),
    quantity INT DEFAULT 0,
    available_quantity INT DEFAULT 0,
    reserved_quantity INT DEFAULT 0,
    unit VARCHAR(20) DEFAULT '個',
    unit_cost DECIMAL(12,2) DEFAULT 0,
    total_cost DECIMAL(15,2) DEFAULT 0,
    location VARCHAR(100),
    batch_no VARCHAR(100),
    production_date DATE,
    expiry_date DATE,
    min_stock_level INT DEFAULT 0,
    max_stock_level INT DEFAULT 0,
    reorder_point INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_inventory_product (product_code),
    INDEX idx_inventory_warehouse (warehouse_code),
    UNIQUE INDEX idx_inventory_product_warehouse (product_code, warehouse_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inventory_transaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_no VARCHAR(50) NOT NULL UNIQUE,
    inventory_id INT,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    warehouse_code VARCHAR(50) NOT NULL,
    warehouse_name VARCHAR(200),
    transaction_type VARCHAR(30) NOT NULL COMMENT 'inbound,outbound,transfer_in,transfer_out,adjustment',
    quantity INT NOT NULL,
    unit_cost DECIMAL(12,2) DEFAULT 0,
    total_cost DECIMAL(15,2) DEFAULT 0,
    balance_before INT DEFAULT 0,
    balance_after INT DEFAULT 0,
    reference_type VARCHAR(50),
    reference_no VARCHAR(100),
    reference_id INT,
    batch_no VARCHAR(100),
    remarks TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_inv_trans_no (transaction_no),
    INDEX idx_inv_trans_product (product_code),
    INDEX idx_inv_trans_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inventory_adjustment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    adjustment_no VARCHAR(50) NOT NULL UNIQUE,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    warehouse_code VARCHAR(50) NOT NULL,
    warehouse_name VARCHAR(200),
    adjustment_type VARCHAR(30) NOT NULL COMMENT 'increase,decrease,stocktaking',
    original_quantity INT NOT NULL,
    adjustment_quantity INT NOT NULL,
    new_quantity INT NOT NULL,
    reason VARCHAR(500),
    status VARCHAR(20) DEFAULT 'draft',
    remarks TEXT,
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_inv_adj_no (adjustment_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stock_alert (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(100) NOT NULL,
    product_name VARCHAR(300),
    warehouse_code VARCHAR(50) NOT NULL,
    warehouse_name VARCHAR(200),
    alert_type VARCHAR(30) NOT NULL COMMENT 'low_stock,overstock,expiring,expired',
    current_quantity INT,
    threshold_quantity INT,
    status VARCHAR(20) DEFAULT 'active',
    remarks TEXT,
    handled_at TIMESTAMP NULL,
    handled_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_alert_product (product_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 220_material_logs_cutting_used_manual.sql (original prefix 220)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- material_logs: 現場未ログイン等で切断CSVに無いが実際は使用済の場合、手動で「切断使用済」と扱う
SET NAMES utf8mb4;

ALTER TABLE `material_logs`
  ADD COLUMN `cutting_used_manual` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '手動で切断使用済と確定' AFTER `note`,
  ADD COLUMN `cutting_used_manual_at` DATETIME NULL DEFAULT NULL COMMENT '手動確定日時' AFTER `cutting_used_manual`,
  ADD COLUMN `cutting_used_manual_by` VARCHAR(100) NULL DEFAULT NULL COMMENT '手動確定ユーザー' AFTER `cutting_used_manual_at`,
  ADD COLUMN `cutting_used_manual_note` VARCHAR(500) NULL DEFAULT NULL COMMENT '手動確定理由・備考' AFTER `cutting_used_manual_by`,
  ADD KEY `idx_material_logs_cutting_used_manual` (`cutting_used_manual`);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 221_production_plan_excel_juban_seisan_junban.sql (original prefix 221)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_plan_excel: 追加 順番；生産順番 允许 0～99（两位数以内的有效数字）
-- 依赖：表已存在且原约束名为 production_plan_excel_chk_1（仅限制 1,2 时）
-- 若库中约束名不同，请先 SHOW CREATE TABLE production_plan_excel; 后改 DROP CHECK 名称。

ALTER TABLE `production_plan_excel`
  DROP CHECK `production_plan_excel_chk_1`;

ALTER TABLE `production_plan_excel`
  ADD COLUMN `順番` tinyint UNSIGNED NULL DEFAULT NULL COMMENT '順番' AFTER `生産順番`;

ALTER TABLE `production_plan_excel`
  ADD CONSTRAINT `production_plan_excel_chk_seisan_junban` CHECK (`生産順番` >= 0 AND `生産順番` <= 99);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 222_production_plan_excel_juban_auto_triggers.sql (original prefix 222)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_plan_excel: 按 日付+加工機 分组，按 生産順番 升序（id 作 tie-break）写入 順番（仅 1/2）
-- 规则：每组第 1 条写 1；第 2 条及以后统一写 2。
-- MySQL 禁止在本表触发器里再次 UPDATE 本表，因此：触发器只写入提示表，由存储过程（或定时 EVENT）执行重算。
-- 依赖：表 production_plan_excel 已存在且含列 日付、加工機、生産順番、順番；MySQL 8.0+（需窗口函数 ROW_NUMBER）。

CREATE TABLE IF NOT EXISTS `production_plan_excel_juban_recalc_hint` (
  `日付` date NOT NULL,
  `加工機` varchar(50) NOT NULL,
  `queued_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`日付`, `加工機`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_ja_0900_as_cs COMMENT = 'production_plan_excel 順番重算队列';

DELIMITER $$

DROP PROCEDURE IF EXISTS `sp_production_plan_excel_recalc_juban_for_hints` $$
CREATE PROCEDURE `sp_production_plan_excel_recalc_juban_for_hints`()
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE v_date DATE;
  DECLARE v_machine VARCHAR(50);
  DECLARE cur CURSOR FOR
    SELECT `日付`, `加工機` FROM `production_plan_excel_juban_recalc_hint`;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  OPEN cur;
  hint_loop: LOOP
    FETCH cur INTO v_date, v_machine;
    IF done = 1 THEN
      LEAVE hint_loop;
    END IF;

    UPDATE `production_plan_excel` AS e
    INNER JOIN (
      SELECT
        id,
        ROW_NUMBER() OVER (
          PARTITION BY `日付`, `加工機`
          ORDER BY `生産順番` ASC, `id` ASC
        ) AS rn
      FROM `production_plan_excel`
      WHERE `日付` = v_date AND `加工機` = v_machine
    ) AS r ON e.id = r.id
    SET e.`順番` = CASE WHEN r.rn = 1 THEN 1 ELSE 2 END;
  END LOOP;
  CLOSE cur;

  TRUNCATE TABLE `production_plan_excel_juban_recalc_hint`;
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_excel_after_insert_juban` $$
CREATE TRIGGER `trg_production_plan_excel_after_insert_juban`
AFTER INSERT ON `production_plan_excel`
FOR EACH ROW
BEGIN
  INSERT IGNORE INTO `production_plan_excel_juban_recalc_hint` (`日付`, `加工機`)
  VALUES (NEW.`日付`, NEW.`加工機`);
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_excel_after_update_juban` $$
CREATE TRIGGER `trg_production_plan_excel_after_update_juban`
AFTER UPDATE ON `production_plan_excel`
FOR EACH ROW
BEGIN
  INSERT IGNORE INTO `production_plan_excel_juban_recalc_hint` (`日付`, `加工機`)
  VALUES (OLD.`日付`, OLD.`加工機`);
  IF NEW.`日付` <> OLD.`日付` OR NEW.`加工機` <> OLD.`加工機` THEN
    INSERT IGNORE INTO `production_plan_excel_juban_recalc_hint` (`日付`, `加工機`)
    VALUES (NEW.`日付`, NEW.`加工機`);
  END IF;
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_excel_after_delete_juban` $$
CREATE TRIGGER `trg_production_plan_excel_after_delete_juban`
AFTER DELETE ON `production_plan_excel`
FOR EACH ROW
BEGIN
  INSERT IGNORE INTO `production_plan_excel_juban_recalc_hint` (`日付`, `加工機`)
  VALUES (OLD.`日付`, OLD.`加工機`);
END $$

DROP EVENT IF EXISTS `evt_production_plan_excel_juban_recalc` $$
CREATE EVENT `evt_production_plan_excel_juban_recalc`
ON SCHEDULE EVERY 5 SECOND
STARTS CURRENT_TIMESTAMP
ON COMPLETION PRESERVE
ENABLE
COMMENT '消费 juban_recalc_hint，重算各组 順番（需 event_scheduler=ON）'
DO
BEGIN
  IF EXISTS (SELECT 1 FROM `production_plan_excel_juban_recalc_hint` LIMIT 1) THEN
    CALL `sp_production_plan_excel_recalc_juban_for_hints`();
  END IF;
END $$

DELIMITER ;

-- 若 EVENT 不执行，请确认：SET GLOBAL event_scheduler = ON;
-- 也可在应用侧在批量写入后执行：CALL sp_production_plan_excel_recalc_juban_for_hints();

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 223_production_plan_updates_trigger_operator_0_99.sql (original prefix 223)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- schedule_details(+production_schedules/machines) -> production_plan_excel 同步触发器
-- 目标：所有设备都可写入（不再限制 machine_type='成型'）
-- 说明：
--   1) 生産順番 使用 production_schedules.order_no，空值按 0，越界按 0~99 截断
--   2) 使用 INSERT ... ON DUPLICATE KEY UPDATE，避免重复键导致写入失败
--   3) 触发器内不抛 SIGNAL，避免业务事务整体回滚

DELIMITER $$

DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_insert` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_update` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_delete` $$

DROP TRIGGER IF EXISTS `trg_schedule_details_after_insert_sync_plan_excel` $$
CREATE TRIGGER `trg_schedule_details_after_insert_sync_plan_excel`
AFTER INSERT ON `schedule_details`
FOR EACH ROW
BEGIN
  DECLARE v_machine_name VARCHAR(100);
  DECLARE v_product_cd VARCHAR(50);
  DECLARE v_product_name VARCHAR(255);
  DECLARE v_order_no INT;

  SELECT m.`machine_name`, ps.`product_cd`, ps.`item_name`, ps.`order_no`
    INTO v_machine_name, v_product_cd, v_product_name, v_order_no
  FROM `production_schedules` ps
  INNER JOIN `machines` m ON m.`id` = ps.`line_id`
  WHERE ps.`id` = NEW.`schedule_id`
  LIMIT 1;

  IF NEW.`schedule_date` IS NOT NULL
     AND v_machine_name IS NOT NULL
     AND v_product_cd IS NOT NULL
     AND v_product_name IS NOT NULL
     AND NEW.`planned_qty` IS NOT NULL THEN
    INSERT INTO `production_plan_excel` (
      `日付`, `加工機`, `製品CD`, `製品名`, `加工計画`, `生産順番`
    ) VALUES (
      NEW.`schedule_date`,
      v_machine_name,
      v_product_cd,
      v_product_name,
      NEW.`planned_qty`,
      CAST(LEAST(GREATEST(COALESCE(v_order_no, 0), 0), 99) AS CHAR)
    )
    ON DUPLICATE KEY UPDATE
      `製品名` = VALUES(`製品名`),
      `加工計画` = VALUES(`加工計画`);
  END IF;
END $$

DROP TRIGGER IF EXISTS `trg_schedule_details_after_update_sync_plan_excel` $$
CREATE TRIGGER `trg_schedule_details_after_update_sync_plan_excel`
AFTER UPDATE ON `schedule_details`
FOR EACH ROW
BEGIN
  DECLARE v_old_machine_name VARCHAR(100);
  DECLARE v_old_product_cd VARCHAR(50);
  DECLARE v_old_order_no INT;
  DECLARE v_new_machine_name VARCHAR(100);
  DECLARE v_new_product_cd VARCHAR(50);
  DECLARE v_new_product_name VARCHAR(255);
  DECLARE v_new_order_no INT;

  SELECT m.`machine_name`, ps.`product_cd`, ps.`order_no`
    INTO v_old_machine_name, v_old_product_cd, v_old_order_no
  FROM `production_schedules` ps
  INNER JOIN `machines` m ON m.`id` = ps.`line_id`
  WHERE ps.`id` = OLD.`schedule_id`
  LIMIT 1;

  SELECT m.`machine_name`, ps.`product_cd`, ps.`item_name`, ps.`order_no`
    INTO v_new_machine_name, v_new_product_cd, v_new_product_name, v_new_order_no
  FROM `production_schedules` ps
  INNER JOIN `machines` m ON m.`id` = ps.`line_id`
  WHERE ps.`id` = NEW.`schedule_id`
  LIMIT 1;

  IF OLD.`schedule_date` IS NOT NULL
     AND v_old_machine_name IS NOT NULL
     AND v_old_product_cd IS NOT NULL THEN
    DELETE FROM `production_plan_excel`
    WHERE `日付` = OLD.`schedule_date`
      AND (`加工機` COLLATE utf8mb4_ja_0900_as_cs) = (v_old_machine_name COLLATE utf8mb4_ja_0900_as_cs)
      AND (`製品CD` COLLATE utf8mb4_ja_0900_as_cs) = (v_old_product_cd COLLATE utf8mb4_ja_0900_as_cs)
      AND (`生産順番` COLLATE utf8mb4_ja_0900_as_cs) = (CAST(LEAST(GREATEST(COALESCE(v_old_order_no, 0), 0), 99) AS CHAR) COLLATE utf8mb4_ja_0900_as_cs);
  END IF;

  IF NEW.`schedule_date` IS NOT NULL
     AND v_new_machine_name IS NOT NULL
     AND v_new_product_cd IS NOT NULL
     AND v_new_product_name IS NOT NULL
     AND NEW.`planned_qty` IS NOT NULL THEN
    INSERT INTO `production_plan_excel` (
      `日付`, `加工機`, `製品CD`, `製品名`, `加工計画`, `生産順番`
    ) VALUES (
      NEW.`schedule_date`,
      v_new_machine_name,
      v_new_product_cd,
      v_new_product_name,
      NEW.`planned_qty`,
      CAST(LEAST(GREATEST(COALESCE(v_new_order_no, 0), 0), 99) AS CHAR)
    )
    ON DUPLICATE KEY UPDATE
      `製品名` = VALUES(`製品名`),
      `加工計画` = VALUES(`加工計画`);
  END IF;
END $$

DROP TRIGGER IF EXISTS `trg_schedule_details_after_delete_sync_plan_excel` $$
CREATE TRIGGER `trg_schedule_details_after_delete_sync_plan_excel`
AFTER DELETE ON `schedule_details`
FOR EACH ROW
BEGIN
  DECLARE v_machine_name VARCHAR(100);
  DECLARE v_product_cd VARCHAR(50);
  DECLARE v_order_no INT;

  SELECT m.`machine_name`, ps.`product_cd`, ps.`order_no`
    INTO v_machine_name, v_product_cd, v_order_no
  FROM `production_schedules` ps
  INNER JOIN `machines` m ON m.`id` = ps.`line_id`
  WHERE ps.`id` = OLD.`schedule_id`
  LIMIT 1;

  IF OLD.`schedule_date` IS NOT NULL
     AND v_machine_name IS NOT NULL
     AND v_product_cd IS NOT NULL THEN
    DELETE FROM `production_plan_excel`
    WHERE `日付` = OLD.`schedule_date`
      AND (`加工機` COLLATE utf8mb4_ja_0900_as_cs) = (v_machine_name COLLATE utf8mb4_ja_0900_as_cs)
      AND (`製品CD` COLLATE utf8mb4_ja_0900_as_cs) = (v_product_cd COLLATE utf8mb4_ja_0900_as_cs)
      AND (`生産順番` COLLATE utf8mb4_ja_0900_as_cs) = (CAST(LEAST(GREATEST(COALESCE(v_order_no, 0), 0), 99) AS CHAR) COLLATE utf8mb4_ja_0900_as_cs);
  END IF;
END $$

DROP TRIGGER IF EXISTS `trg_production_schedules_after_update_sync_plan_excel` $$
CREATE TRIGGER `trg_production_schedules_after_update_sync_plan_excel`
AFTER UPDATE ON `production_schedules`
FOR EACH ROW
BEGIN
  DECLARE v_old_machine_name VARCHAR(100);
  DECLARE v_new_machine_name VARCHAR(100);

  SELECT `machine_name`
    INTO v_old_machine_name
  FROM `machines`
  WHERE `id` = OLD.`line_id`
  LIMIT 1;

  SELECT `machine_name`
    INTO v_new_machine_name
  FROM `machines`
  WHERE `id` = NEW.`line_id`
  LIMIT 1;

  IF v_old_machine_name IS NOT NULL AND OLD.`product_cd` IS NOT NULL THEN
    DELETE ppe
    FROM `production_plan_excel` ppe
    INNER JOIN `schedule_details` sd
      ON sd.`schedule_id` = OLD.`id` AND sd.`schedule_date` = ppe.`日付`
    WHERE (ppe.`加工機` COLLATE utf8mb4_ja_0900_as_cs) = (v_old_machine_name COLLATE utf8mb4_ja_0900_as_cs)
      AND (ppe.`製品CD` COLLATE utf8mb4_ja_0900_as_cs) = (OLD.`product_cd` COLLATE utf8mb4_ja_0900_as_cs)
      AND (ppe.`生産順番` COLLATE utf8mb4_ja_0900_as_cs) = (CAST(LEAST(GREATEST(COALESCE(OLD.`order_no`, 0), 0), 99) AS CHAR) COLLATE utf8mb4_ja_0900_as_cs);
  END IF;

  IF v_new_machine_name IS NOT NULL
     AND NEW.`product_cd` IS NOT NULL
     AND NEW.`item_name` IS NOT NULL THEN
    INSERT INTO `production_plan_excel` (`日付`, `加工機`, `製品CD`, `製品名`, `加工計画`, `生産順番`)
    SELECT
      sd.`schedule_date`,
      v_new_machine_name,
      NEW.`product_cd`,
      NEW.`item_name`,
      sd.`planned_qty`,
      CAST(LEAST(GREATEST(COALESCE(NEW.`order_no`, 0), 0), 99) AS CHAR)
    FROM `schedule_details` sd
    WHERE sd.`schedule_id` = NEW.`id`
    ON DUPLICATE KEY UPDATE
      `製品名` = VALUES(`製品名`),
      `加工計画` = VALUES(`加工計画`);
  END IF;
END $$

DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_insert` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_update` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_delete` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_insert_legacy` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_update_legacy` $$
DROP TRIGGER IF EXISTS `trg_production_plan_updates_after_delete_legacy` $$

DELIMITER ;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 224_part_purchase_tables.sql (original prefix 224)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 部品購買・在庫：主表作成、廃止テーブル削除、既存 part_stock の列整合（224–228 を統合）
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 1) 部品在庫メイン（material_stock と同形・拡張）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `part_stock` (
  `id` int NOT NULL AUTO_INCREMENT,
  `part_cd` varchar(50) NOT NULL COMMENT '部品CD',
  `part_name` varchar(50) NOT NULL COMMENT '部品名',
  `date` date NOT NULL DEFAULT '2025-01-01' COMMENT '日付',
  `initial_stock` int DEFAULT 0 COMMENT '初期在庫',
  `current_stock` int DEFAULT 0 COMMENT '現在在庫',
  `planned_usage` int DEFAULT 0 COMMENT '使用数',
  `usage_plan_qty` int NOT NULL DEFAULT 0 COMMENT '部品使用計画数量',
  `stock_trend` int NOT NULL DEFAULT 0 COMMENT '在庫推移',
  `adjustment_quantity` int DEFAULT 0 COMMENT '調整数',
  `standard_spec` varchar(50) DEFAULT '' COMMENT '規格・分類',
  `unit` varchar(20) DEFAULT NULL COMMENT '単位',
  `unit_price` decimal(15,2) DEFAULT 0.00 COMMENT '単価',
  `pieces_per_bundle` int DEFAULT 0 COMMENT '梱包単位数',
  `supplier_cd` varchar(15) DEFAULT NULL COMMENT '仕入先CD',
  `supplier_name` varchar(50) DEFAULT NULL COMMENT '仕入先名',
  `lead_time` int DEFAULT 0 COMMENT 'リードタイム(日)',
  `order_quantity` int DEFAULT 0 COMMENT '注文数',
  `order_bundle_quantity` int DEFAULT 0 COMMENT '注文細目数',
  `order_amount` decimal(15,2) DEFAULT 0.00 COMMENT '注文金額',
  `last_updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `remarks` varchar(50) DEFAULT '' COMMENT '備考',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_part_stock_cd_date` (`part_cd`, `date`),
  KEY `idx_part_stock_cd` (`part_cd`),
  KEY `idx_part_stock_supplier` (`supplier_cd`),
  KEY `idx_part_stock_current` (`current_stock`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部品在庫メイン';

-- ---------------------------------------------------------------------------
-- 2) 廃止テーブル削除（主表 part_stock のみ運用）
-- ---------------------------------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `part_stock_sub`;
SET FOREIGN_KEY_CHECKS = 1;

DROP TABLE IF EXISTS `part_demand_daily`;

DROP TABLE IF EXISTS `part_logs`;
DROP TABLE IF EXISTS `part_inspection_master`;

-- ---------------------------------------------------------------------------
-- 3) 既存 DB の part_stock：列の追加・旧列削除（列の有無で分岐）
-- ---------------------------------------------------------------------------
SET @db = DATABASE();

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'usage_plan_qty'
);
SET @sql := IF(@exist = 0,
  'ALTER TABLE part_stock ADD COLUMN `usage_plan_qty` int NOT NULL DEFAULT 0 COMMENT ''部品使用計画数量'' AFTER `planned_usage`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'stock_trend'
);
SET @sql := IF(@exist = 0,
  'ALTER TABLE part_stock ADD COLUMN `stock_trend` int NOT NULL DEFAULT 0 COMMENT ''在庫推移'' AFTER `usage_plan_qty`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'safety_stock'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `safety_stock`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'long_weight'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `long_weight`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'max_stock'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `max_stock`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'bundle_quantity'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `bundle_quantity`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'part_stock' AND COLUMN_NAME = 'bundle_weight'
);
SET @sql := IF(@exist > 0, 'ALTER TABLE part_stock DROP COLUMN `bundle_weight`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 225_aps_line_replan_anchors.sql (original prefix 225)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 設備ごとの APS 順次再計算アンカー日（成型計画等で保存し、replan-sequence で優先使用）
CREATE TABLE IF NOT EXISTS aps_line_replan_anchors (
  line_id INT NOT NULL COMMENT 'machines.id',
  anchor_date DATE NOT NULL COMMENT '順次再計算の開始暦日（日本日付想定）',
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (line_id),
  CONSTRAINT fk_aps_line_replan_anchors_machine FOREIGN KEY (line_id) REFERENCES machines (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='設備別再計算アンカー日';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 226_schedule_details_defect_qty.sql (original prefix 226)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- schedule_details に不良数（defect_qty）を追加し、
-- remaining_qty = planned_qty - actual_qty - defect_qty とする（負値可）。
-- 成型不良：transaction_type=不良 かつ process_cd=KT04、TRIM(target_cd)=TRIM(工単.product_cd)、DATE(transaction_time)=schedule_date で quantity を合算。
-- 在庫ログに machine_cd が無くても同期する（実績は従来どおり machine 一致）。

SET NAMES utf8mb4;

SET @dbname = DATABASE();

-- 1) schedule_details に defect_qty
SET @col_exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'schedule_details' AND COLUMN_NAME = 'defect_qty'
);
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE `schedule_details` ADD COLUMN `defect_qty` int NOT NULL DEFAULT 0 COMMENT ''日次不良数（stock_transaction_logs 不良同期）'' AFTER `actual_qty`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2) remaining トリガー（良品・不良を差し引き）
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bi`;
DROP TRIGGER IF EXISTS `tg_schedule_details_remaining_bu`;

DELIMITER $$
CREATE TRIGGER `tg_schedule_details_remaining_bi`
BEFORE INSERT ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0) - COALESCE(NEW.defect_qty, 0);
END$$

CREATE TRIGGER `tg_schedule_details_remaining_bu`
BEFORE UPDATE ON `schedule_details`
FOR EACH ROW
BEGIN
    SET NEW.remaining_qty = COALESCE(NEW.planned_qty, 0) - COALESCE(NEW.actual_qty, 0) - COALESCE(NEW.defect_qty, 0);
END$$
DELIMITER ;

-- 3) 在庫ログ → schedule_details（実績・不良）
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ai`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_au`;
DROP TRIGGER IF EXISTS `tg_stl_sync_schedule_details_ad`;

DELIMITER $$

CREATE TRIGGER `tg_stl_sync_schedule_details_ai`
AFTER INSERT ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF NEW.transaction_time IS NOT NULL AND NEW.target_cd IS NOT NULL THEN
        IF NEW.transaction_type = '実績' AND NEW.machine_cd IS NOT NULL THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    stl.machine_cd AS machine_cd,
                    stl.target_cd AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS qty
                FROM stock_transaction_logs stl
                WHERE stl.transaction_type = '実績'
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
                  AND stl.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
                  AND stl.target_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
            SET sd.actual_qty = COALESCE(agg.qty, 0)
            WHERE sd.schedule_date = DATE(NEW.transaction_time)
              AND m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
              AND ps.product_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci;
        END IF;

        IF NEW.transaction_type = '不良'
           AND TRIM(IFNULL(NEW.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    TRIM(stl.target_cd) AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS dq
                FROM stock_transaction_logs stl
                WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
                  AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
                  AND TRIM(stl.target_cd) COLLATE utf8mb4_unicode_ci = TRIM(NEW.target_cd) COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
            SET sd.defect_qty = COALESCE(agg.dq, 0)
            WHERE sd.schedule_date = DATE(NEW.transaction_time)
              AND TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci = TRIM(NEW.target_cd) COLLATE utf8mb4_unicode_ci
              AND (NEW.machine_cd IS NULL OR m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci);
        END IF;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_au`
AFTER UPDATE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF OLD.transaction_time IS NOT NULL AND OLD.target_cd IS NOT NULL THEN
        IF OLD.transaction_type = '実績' AND OLD.machine_cd IS NOT NULL THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    stl.machine_cd AS machine_cd,
                    stl.target_cd AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS qty
                FROM stock_transaction_logs stl
                WHERE stl.transaction_type = '実績'
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
                  AND stl.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
                  AND stl.target_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
            SET sd.actual_qty = COALESCE(agg.qty, 0)
            WHERE sd.schedule_date = DATE(OLD.transaction_time)
              AND m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
              AND ps.product_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci;
        END IF;
        IF OLD.transaction_type = '不良'
           AND TRIM(IFNULL(OLD.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    TRIM(stl.target_cd) AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS dq
                FROM stock_transaction_logs stl
                WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
                  AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
                  AND TRIM(stl.target_cd) COLLATE utf8mb4_unicode_ci = TRIM(OLD.target_cd) COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
            SET sd.defect_qty = COALESCE(agg.dq, 0)
            WHERE sd.schedule_date = DATE(OLD.transaction_time)
              AND TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci = TRIM(OLD.target_cd) COLLATE utf8mb4_unicode_ci
              AND (OLD.machine_cd IS NULL OR m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci);
        END IF;
    END IF;

    IF NEW.transaction_time IS NOT NULL AND NEW.target_cd IS NOT NULL THEN
        IF NEW.transaction_type = '実績' AND NEW.machine_cd IS NOT NULL THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    stl.machine_cd AS machine_cd,
                    stl.target_cd AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS qty
                FROM stock_transaction_logs stl
                WHERE stl.transaction_type = '実績'
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
                  AND stl.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
                  AND stl.target_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
            SET sd.actual_qty = COALESCE(agg.qty, 0)
            WHERE sd.schedule_date = DATE(NEW.transaction_time)
              AND m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci
              AND ps.product_cd COLLATE utf8mb4_unicode_ci = NEW.target_cd COLLATE utf8mb4_unicode_ci;
        END IF;
        IF NEW.transaction_type = '不良'
           AND TRIM(IFNULL(NEW.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    TRIM(stl.target_cd) AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS dq
                FROM stock_transaction_logs stl
                WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
                  AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(NEW.transaction_time)
                  AND TRIM(stl.target_cd) COLLATE utf8mb4_unicode_ci = TRIM(NEW.target_cd) COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
            SET sd.defect_qty = COALESCE(agg.dq, 0)
            WHERE sd.schedule_date = DATE(NEW.transaction_time)
              AND TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci = TRIM(NEW.target_cd) COLLATE utf8mb4_unicode_ci
              AND (NEW.machine_cd IS NULL OR m.machine_cd COLLATE utf8mb4_unicode_ci = NEW.machine_cd COLLATE utf8mb4_unicode_ci);
        END IF;
    END IF;
END$$

CREATE TRIGGER `tg_stl_sync_schedule_details_ad`
AFTER DELETE ON `stock_transaction_logs`
FOR EACH ROW
BEGIN
    IF OLD.transaction_time IS NOT NULL AND OLD.target_cd IS NOT NULL THEN
        IF OLD.transaction_type = '実績' AND OLD.machine_cd IS NOT NULL THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    stl.machine_cd AS machine_cd,
                    stl.target_cd AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS qty
                FROM stock_transaction_logs stl
                WHERE stl.transaction_type = '実績'
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
                  AND stl.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
                  AND stl.target_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), stl.machine_cd, stl.target_cd
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.machine_cd COLLATE utf8mb4_unicode_ci = m.machine_cd COLLATE utf8mb4_unicode_ci
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = ps.product_cd COLLATE utf8mb4_unicode_ci
            SET sd.actual_qty = COALESCE(agg.qty, 0)
            WHERE sd.schedule_date = DATE(OLD.transaction_time)
              AND m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci
              AND ps.product_cd COLLATE utf8mb4_unicode_ci = OLD.target_cd COLLATE utf8mb4_unicode_ci;
        END IF;
        IF OLD.transaction_type = '不良'
           AND TRIM(IFNULL(OLD.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci THEN
            UPDATE schedule_details sd
            JOIN production_schedules ps ON ps.id = sd.schedule_id
            JOIN machines m ON m.id = ps.line_id
            LEFT JOIN (
                SELECT
                    DATE(stl.transaction_time) AS d,
                    TRIM(stl.target_cd) AS product_cd,
                    COALESCE(SUM(stl.quantity), 0) AS dq
                FROM stock_transaction_logs stl
                WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
                  AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
                  AND stl.transaction_time IS NOT NULL
                  AND DATE(stl.transaction_time) = DATE(OLD.transaction_time)
                  AND TRIM(stl.target_cd) COLLATE utf8mb4_unicode_ci = TRIM(OLD.target_cd) COLLATE utf8mb4_unicode_ci
                GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
            ) agg
              ON agg.d = sd.schedule_date
             AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
            SET sd.defect_qty = COALESCE(agg.dq, 0)
            WHERE sd.schedule_date = DATE(OLD.transaction_time)
              AND TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci = TRIM(OLD.target_cd) COLLATE utf8mb4_unicode_ci
              AND (OLD.machine_cd IS NULL OR m.machine_cd COLLATE utf8mb4_unicode_ci = OLD.machine_cd COLLATE utf8mb4_unicode_ci);
        END IF;
    END IF;
END$$

DELIMITER ;

-- 4) 既存明細の不良・残を一括補正（defect_qty 列追加直後）
UPDATE schedule_details sd
JOIN production_schedules ps ON ps.id = sd.schedule_id
JOIN machines m ON m.id = ps.line_id
LEFT JOIN (
    SELECT
        DATE(stl.transaction_time) AS d,
        TRIM(stl.target_cd) AS product_cd,
        COALESCE(SUM(stl.quantity), 0) AS dq
    FROM stock_transaction_logs stl
    WHERE TRIM(IFNULL(stl.transaction_type, '')) COLLATE utf8mb4_unicode_ci = '不良' COLLATE utf8mb4_unicode_ci
      AND TRIM(IFNULL(stl.process_cd, '')) COLLATE utf8mb4_unicode_ci = 'KT04' COLLATE utf8mb4_unicode_ci
      AND stl.transaction_time IS NOT NULL
      AND stl.target_cd IS NOT NULL
    GROUP BY DATE(stl.transaction_time), TRIM(stl.target_cd)
) agg
  ON agg.d = sd.schedule_date
 AND agg.product_cd COLLATE utf8mb4_unicode_ci = TRIM(ps.product_cd) COLLATE utf8mb4_unicode_ci
SET sd.defect_qty = COALESCE(agg.dq, 0);

UPDATE schedule_details
SET remaining_qty = COALESCE(planned_qty, 0) - COALESCE(actual_qty, 0) - COALESCE(defect_qty, 0);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 227_aps_batch_plans_upstream_defect_qty.sql (original prefix 227)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- aps_batch_plans：前工程（切断 + 面取）不良合計をロット単位で保持し、成型ロット計画（planned_quantity）の上限に反映する。
SET NAMES utf8mb4;

SET @dbname = DATABASE();

SET @col_exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'aps_batch_plans' AND COLUMN_NAME = 'upstream_defect_qty'
);
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE `aps_batch_plans` ADD COLUMN `upstream_defect_qty` int NOT NULL DEFAULT 0 COMMENT ''前工程不良合計（cutting_management + chamfering_management、management_code 照合）'' AFTER `planned_quantity`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 228_cutting_management_aps_batch_plan_id.sql (original prefix 228)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- cutting_management に APS ロット安定キー（aps_batch_plans.id）を追加し、
-- 前工程不良集計・顺位変更後も instruction_plans / APS と追跡可能にする。
SET NAMES utf8mb4;

SET @dbname = DATABASE();

SET @col_exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'cutting_management' AND COLUMN_NAME = 'aps_batch_plan_id'
);
SET @sql := IF(@col_exists = 0,
  'ALTER TABLE `cutting_management` ADD COLUMN `aps_batch_plan_id` int NULL DEFAULT NULL COMMENT ''APS ロット（aps_batch_plans.id）参照'' AFTER `management_code`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'cutting_management' AND INDEX_NAME = 'idx_cutting_aps_batch_plan_id'
);
SET @sql2 := IF(@idx_exists = 0,
  'CREATE INDEX `idx_cutting_aps_batch_plan_id` ON `cutting_management` (`aps_batch_plan_id`)',
  'SELECT 1');
PREPARE stmt2 FROM @sql2; EXECUTE stmt2; DEALLOCATE PREPARE stmt2;

-- FK（存在時のみ付与）
SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = @dbname AND TABLE_NAME = 'cutting_management'
    AND CONSTRAINT_NAME = 'fk_cutting_management_aps_batch_plan'
);
SET @sql3 := IF(@fk_exists = 0,
  'ALTER TABLE `cutting_management` ADD CONSTRAINT `fk_cutting_management_aps_batch_plan` FOREIGN KEY (`aps_batch_plan_id`) REFERENCES `aps_batch_plans` (`id`) ON DELETE SET NULL ON UPDATE CASCADE',
  'SELECT 1');
PREPARE stmt3 FROM @sql3; EXECUTE stmt3; DEALLOCATE PREPARE stmt3;

-- 既存行のベストエフォート突合（品番・ロット・生産月）。複数 aps_batch_plans が一致する場合は MIN(id) を採用。
UPDATE `cutting_management` cm
INNER JOIN (
  SELECT MIN(`id`) AS `id`, `product_cd`, `lot_number`, `production_month`
  FROM `aps_batch_plans`
  GROUP BY `product_cd`, `lot_number`, `production_month`
) abp
  ON TRIM(COALESCE(cm.`product_cd`,'')) = TRIM(COALESCE(abp.`product_cd`,''))
 AND TRIM(COALESCE(cm.`lot_number`,'')) = TRIM(COALESCE(abp.`lot_number`,''))
 AND cm.`production_month` = abp.`production_month`
SET cm.`aps_batch_plan_id` = abp.`id`
WHERE cm.`aps_batch_plan_id` IS NULL;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 229_production_plan_excel_kensaku_use_juban.sql (original prefix 229)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_plan_excel: 検索 生成列を「年月日 + 加工機後方2桁 + 順番」に修正（誤って 生産順番 を連結していた）
-- 依赖：表 production_plan_excel に列 日付、加工機、順番、検索 が存在すること。
-- 順番 が NULL の行（未重算など）は末尾を空文字にし、CONCAT 全体が NULL にならないようにする。

ALTER TABLE `production_plan_excel`
  MODIFY COLUMN `検索` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_ja_0900_as_cs
  GENERATED ALWAYS AS (
    concat(
      date_format(`日付`, '%Y%m%d'),
      right(`加工機`, 2),
      coalesce(cast(`順番` AS CHAR), '')
    )
  ) STORED NULL COMMENT '検索キー (自動生成: 年月日 + 加工機後方2桁 + 順番)';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 230_product_cost_cumulative_snapshots.sql (original prefix 230)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 製品×ルート 累計単価スナップショット / 一括再計算ジョブ
-- 適用場面：全新庫 / 老庫升級（幂等）
--
-- 【必須】本ファイルを接続先 DB（例: eams_db）で実行しないと、
--   `product_cost_cumulative_snapshots` 不存在 (1146) となり API が失敗します。
--   例: mysql -u USER -p eams_db < backend/database/migrations/230_product_cost_cumulative_snapshots.sql
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 累計単価スナップショット（画面「単価累計（工程完了時点）」の行を保存）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `product_cost_cumulative_snapshots` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `snapshot_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '同一スナップショットのグループID（UUID）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品CD',
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートCD',
  `bom_header_id` int DEFAULT NULL COMMENT 'スナップショット時のBOMヘッダID',
  `row_kind` varchar(20) NOT NULL DEFAULT 'route_step' COMMENT 'route_step / unassigned',
  `row_order` int NOT NULL DEFAULT 0 COMMENT '表示順（stepソート＋unassignedは最後）',
  `step_no` int DEFAULT NULL COMMENT 'ルートstep_no（unassignedはNULL）',
  `process_cd` varchar(50) DEFAULT NULL COMMENT '工程CD',
  `stage_label` varchar(200) DEFAULT NULL COMMENT '表示用ラベル（〜 xx 工程完了時点）',
  `material_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '材料単価（当段）',
  `part_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '部品単価（当段）',
  `process_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '工程単価（当段）',
  `stage_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '当段増分',
  `cumulative_unit_price` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '累計単価',
  `currency` varchar(10) NOT NULL DEFAULT 'JPY',
  `is_latest` tinyint(1) NOT NULL DEFAULT 0 COMMENT '同一 product+route の最新フラグ',
  `source_job_id` bigint DEFAULT NULL COMMENT '生成元ジョブID',
  `remarks` text,
  `created_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_pcs_group` (`snapshot_id`),
  KEY `idx_pcs_pr` (`product_cd`, `route_cd`),
  KEY `idx_pcs_latest` (`product_cd`, `route_cd`, `is_latest`),
  KEY `idx_pcs_created` (`product_cd`, `route_cd`, `created_at`),
  KEY `idx_pcs_job` (`source_job_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品×ルート 累計単価スナップショット';


-- ---------------------------------------------------------------------------
-- 一括再計算ジョブ（非同期）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `product_cost_recalc_jobs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `status` varchar(20) NOT NULL DEFAULT 'queued' COMMENT 'queued/running/completed/failed/partial',
  `mode` varchar(30) NOT NULL DEFAULT 'append_snapshot' COMMENT 'append_snapshot / replace_current',
  `scope` varchar(30) NOT NULL DEFAULT 'selected' COMMENT 'selected / all',
  `total_items` int NOT NULL DEFAULT 0,
  `done_items` int NOT NULL DEFAULT 0,
  `success_items` int NOT NULL DEFAULT 0,
  `failed_items` int NOT NULL DEFAULT 0,
  `payload_json` longtext COMMENT '入力（製品リスト等）JSON',
  `error_log` longtext COMMENT '失敗明細JSON（配列）',
  `result_snapshot_ids_json` longtext COMMENT '生成スナップショットIDリストJSON',
  `message` varchar(500) DEFAULT NULL COMMENT '進捗/エラー概要',
  `created_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `started_at` datetime DEFAULT NULL,
  `finished_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pcrj_status` (`status`),
  KEY `idx_pcrj_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='累計単価 一括再計算ジョブ';

-- 既に decimal(18,6) で `product_cost_cumulative_snapshots` を作成済みの場合のみ、
-- 次を対象 DB で実行して金額列を 2 桁に揃える（新規作成は上記 CREATE でそのまま 18,2）。
-- ALTER TABLE `product_cost_cumulative_snapshots`
--   MODIFY `material_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '材料単価（当段）',
--   MODIFY `part_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '部品単価（当段）',
--   MODIFY `process_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '工程単価（当段）',
--   MODIFY `stage_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '当段増分',
--   MODIFY `cumulative_unit_price` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '累計単価';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 231_products_add_kind.sql (original prefix 231)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

SET NAMES utf8mb4;

SET @col_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'products'
    AND COLUMN_NAME = 'kind'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE `products` ADD COLUMN `kind` varchar(50) NULL DEFAULT NULL COMMENT ''分類'' AFTER `category`',
  'SELECT ''Column kind already exists'' AS msg'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 232_order_daily_add_part_number.sql (original prefix 232)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ================================================================
-- order_daily テーブルに part_number カラムを追加（EDI かんばん取込で使用）
-- Version: 232
-- ================================================================

SET NAMES utf8mb4;

-- 1) part_number カラム追加（既に存在する場合はスキップ）
SET @col_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'order_daily'
    AND COLUMN_NAME = 'part_number'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE `order_daily` ADD COLUMN `part_number` varchar(50) NULL DEFAULT NULL COMMENT ''EDI かんばん品番（hinban）'' AFTER `product_cd`',
  'SELECT ''Column part_number already exists'' AS msg'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2) part_number にインデックスを付与（EDI 取込時の検索高速化）
SET @idx_exists := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'order_daily'
    AND INDEX_NAME = 'idx_order_daily_part_number'
);

SET @idx_ddl := IF(
  @idx_exists = 0,
  'CREATE INDEX `idx_order_daily_part_number` ON `order_daily` (`part_number`)',
  'SELECT ''Index idx_order_daily_part_number already exists'' AS msg'
);

PREPARE stmt2 FROM @idx_ddl;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 234_production_schedules_forced_start_date.sql (original prefix 234)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ================================================================
-- production_schedules に forced_start_date を追加（開始日強制指定）
-- Version: 234
-- ================================================================

SET NAMES utf8mb4;

SET @col_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'production_schedules'
    AND COLUMN_NAME = 'forced_start_date'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE `production_schedules` ADD COLUMN `forced_start_date` DATE NULL DEFAULT NULL COMMENT ''排産開始日の強制下限（NULL=未指定）'' AFTER `material_date`',
  'SELECT ''Column forced_start_date already exists'' AS msg'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 235_shipping_warehouse_daily_stock.sql (original prefix 235)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ================================================================
-- 出荷管理：倉庫日次在庫テーブル作成
-- Version: 235
-- ================================================================

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `shipping_warehouse_daily_stock` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `product_cd` VARCHAR(50) NOT NULL COMMENT '製品CD',
  `product_name` VARCHAR(255) NOT NULL COMMENT '製品名',
  `destination_cd` VARCHAR(50) NOT NULL COMMENT '納入先CD',
  `work_date` DATE NOT NULL COMMENT '日付',
  `weekday` VARCHAR(10) NOT NULL COMMENT '曜日',
  `order_qty` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '受注数',
  `forecast_qty` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '内示数',
  `warehouse_carryover` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫繰越',
  `warehouse_actual` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫実績',
  `warehouse_defect` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫不良',
  `warehouse_disposal` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫廃棄',
  `warehouse_hold` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫保留品',
  `warehouse_stock` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫在庫',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_shipping_warehouse_daily_stock` (`destination_cd`, `product_cd`, `work_date`),
  KEY `idx_shipping_warehouse_daily_stock_work_date` (`work_date`),
  KEY `idx_shipping_warehouse_daily_stock_product_cd` (`product_cd`),
  KEY `idx_shipping_warehouse_daily_stock_destination_cd` (`destination_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='倉庫日次在庫';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 236_shipping_items_picking_log_matched.sql (original prefix 236)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- shipping_log.picking_no と shipping_no_p が一致するログが存在する場合 1、否则 0
-- PickingLog 取込・ログ削除時にアプリ側で再計算する
--
-- 性能: 相関 EXISTS は shipping_items 行ごとに shipping_log を探しに行きやすい。
--       shipping_log から picking_no を一度だけ集約した派生表と LEFT JOIN する方が、
--       idx_picking_no を活かしやすく大規模データで速くなることが多い。
--       （028_shipping_log.sql の KEY idx_picking_no (picking_no) を前提）

ALTER TABLE shipping_items
  ADD COLUMN picking_log_matched TINYINT(1) NOT NULL DEFAULT 0
    COMMENT 'shipping_log に picking_no=shipping_no_p の行があれば1否则0'
  AFTER status;

-- MySQL 8.0.12+ で列追加のみが INSTANT 対象の場合は、運用で次のようにすると ALTER 自体も短縮できる場合あり:
-- ALTER TABLE shipping_items ADD COLUMN ... ALGORITHM=INSTANT;

UPDATE shipping_items si
LEFT JOIN (
  SELECT picking_no
  FROM shipping_log
  WHERE picking_no IS NOT NULL AND picking_no != ''
  GROUP BY picking_no
) sl ON sl.picking_no = si.shipping_no_p
SET si.picking_log_matched = IF(sl.picking_no IS NULL, 0, 1)
WHERE si.shipping_no_p IS NOT NULL AND si.shipping_no_p != '';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 236_shipping_warehouse_daily_stock_destination_cd.sql (original prefix 236)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ================================================================
-- shipping_warehouse_daily_stock に destination_cd（納入先CD）を追加し、
-- UNIQUE を (destination_cd, product_cd, work_date) に更新（旧235適用済みDB向け）
-- Version: 236
-- ================================================================

SET NAMES utf8mb4;

-- 1) destination_cd カラム（存在しなければ追加）
SET @col_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'shipping_warehouse_daily_stock'
    AND COLUMN_NAME = 'destination_cd'
);

SET @ddl := IF(
  @col_exists = 0,
  'ALTER TABLE `shipping_warehouse_daily_stock` ADD COLUMN `destination_cd` varchar(50) NOT NULL DEFAULT '''' COMMENT ''納入先CD'' AFTER `product_name`',
  'SELECT ''Column destination_cd already exists'' AS msg'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2) 旧 UNIQUE(product_cd, work_date) のみの場合は DROP
SET @uk_col_count := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'shipping_warehouse_daily_stock'
    AND INDEX_NAME = 'uk_shipping_warehouse_daily_stock'
);

SET @ddl_drop := IF(
  @uk_col_count = 2,
  'ALTER TABLE `shipping_warehouse_daily_stock` DROP INDEX `uk_shipping_warehouse_daily_stock`',
  'SELECT ''Skip drop uk (not old 2-column index)'' AS msg'
);

PREPARE stmt2 FROM @ddl_drop;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- 3) UNIQUE が無ければ (destination_cd, product_cd, work_date) で作成
SET @uk_now := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'shipping_warehouse_daily_stock'
    AND INDEX_NAME = 'uk_shipping_warehouse_daily_stock'
);

SET @ddl_add_uk := IF(
  @uk_now = 0,
  'ALTER TABLE `shipping_warehouse_daily_stock` ADD UNIQUE KEY `uk_shipping_warehouse_daily_stock` (`destination_cd`, `product_cd`, `work_date`)',
  'SELECT ''UK uk_shipping_warehouse_daily_stock already exists'' AS msg'
);

PREPARE stmt3 FROM @ddl_add_uk;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;

-- 4) 納入先CD 検索用インデックス
SET @idx_exists := (
  SELECT COUNT(*)
  FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'shipping_warehouse_daily_stock'
    AND INDEX_NAME = 'idx_shipping_warehouse_daily_stock_destination_cd'
);

SET @ddl_idx := IF(
  @idx_exists = 0,
  'CREATE INDEX `idx_shipping_warehouse_daily_stock_destination_cd` ON `shipping_warehouse_daily_stock` (`destination_cd`)',
  'SELECT ''Index idx_shipping_warehouse_daily_stock_destination_cd already exists'' AS msg'
);

PREPARE stmt4 FROM @ddl_idx;
EXECUTE stmt4;
DEALLOCATE PREPARE stmt4;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 237_cutting_instruction_notes.sql (original prefix 237)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- cutting instruction notes（メモ/TODO）
-- ページ（生産ロット一覧）右上の「メモ」アイコンで使用

CREATE TABLE IF NOT EXISTS `cutting_instruction_notes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `scope` varchar(50) NOT NULL DEFAULT 'cutting_instruction',
  `content` varchar(200) NOT NULL,
  `is_done` tinyint NOT NULL DEFAULT 0 COMMENT '0:未完了 1:完了',
  `created_by` varchar(50) NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_scope_is_done_created_at` (`scope`, `is_done`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 238_aps_plating_planning_menu.sql (original prefix 238)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS: 生産計画作成 配下に「メッキ計画作成」を追加

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'APS_PLATING_PLANNING', 'メッキ計画作成', m.id, '/aps/plating-planning', 'Operation', 4
FROM menus m
WHERE m.code = 'APS_PRODUCTION_PLAN_CREATE'
LIMIT 1;

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, child.id
FROM role_menu_permissions rmp
INNER JOIN menus parent ON parent.id = rmp.menu_id AND parent.code = 'APS_PRODUCTION_PLAN_CREATE'
INNER JOIN menus child ON child.code = 'APS_PLATING_PLANNING';

INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT (SELECT id FROM roles WHERE name = '管理者' LIMIT 1), id
FROM menus
WHERE code = 'APS_PLATING_PLANNING';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 239_aps_plating_plan_drafts.sql (original prefix 239)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS メッキ計画（第③区域ドラフト）保存テーブル

CREATE TABLE IF NOT EXISTS aps_plating_plan_drafts (
  id INT NOT NULL AUTO_INCREMENT,
  plan_date DATE NOT NULL,
  version_no INT NOT NULL DEFAULT 1,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  daily_minutes INT NOT NULL DEFAULT 600,
  jigs_per_lap INT NOT NULL DEFAULT 100,
  minutes_per_lap INT NOT NULL DEFAULT 100,
  total_slots INT NOT NULL DEFAULT 0,
  used_slots INT NOT NULL DEFAULT 0,
  remain_slots INT NOT NULL DEFAULT 0,
  created_by VARCHAR(50) NULL,
  updated_by VARCHAR(50) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_aps_plating_plan_drafts_date_ver (plan_date, version_no),
  KEY idx_aps_plating_plan_drafts_date (plan_date),
  KEY idx_aps_plating_plan_drafts_status (status)
);

CREATE TABLE IF NOT EXISTS aps_plating_plan_draft_items (
  id BIGINT NOT NULL AUTO_INCREMENT,
  draft_id INT NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  product_cd VARCHAR(64) NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  plating_machine VARCHAR(64) NOT NULL,
  kake DECIMAL(10,2) NOT NULL DEFAULT 0,
  qty INT NOT NULL DEFAULT 0,
  slots INT NOT NULL DEFAULT 0,
  source_type VARCHAR(32) NOT NULL,
  source_row_key VARCHAR(128) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_aps_plating_plan_draft_items_draft_sort (draft_id, sort_order),
  KEY idx_aps_plating_plan_draft_items_product_cd (product_cd),
  CONSTRAINT fk_aps_plating_plan_draft_items_draft
    FOREIGN KEY (draft_id) REFERENCES aps_plating_plan_drafts(id)
    ON DELETE CASCADE
);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 240_aps_plating_plan_draft_items_work_date.sql (original prefix 240)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

ALTER TABLE aps_plating_plan_draft_items
  ADD COLUMN work_date DATE NULL AFTER sort_order;

CREATE INDEX idx_aps_plating_plan_draft_items_work_date
  ON aps_plating_plan_draft_items (work_date);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 242_machines_add_available_qty.sql (original prefix 242)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- machines.available_qty（再実行しても 1060 にならない）
SET @col_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'machines'
    AND COLUMN_NAME = 'available_qty'
);

SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE machines ADD COLUMN available_qty INT NULL DEFAULT 0 COMMENT ''可用数量'' AFTER efficiency',
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 243_aps_plating_plan_board_cards.sql (original prefix 243)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- APS メッキ計画 第④看板枠（周回内順序）子表：与草稿主表 plan_date / version 一并落库便于查询与追溯

CREATE TABLE IF NOT EXISTS aps_plating_plan_board_cards (
  id BIGINT NOT NULL AUTO_INCREMENT,
  draft_id INT NOT NULL,
  plan_date DATE NOT NULL COMMENT '计划日（与 aps_plating_plan_drafts.plan_date 冗余，便于按日查询）',
  draft_version_no INT NOT NULL DEFAULT 1 COMMENT '写入时草稿版本号（与主表 version_no 快照一致）',
  work_date DATE NULL COMMENT '作業日；NULL 表示沿用 plan_date 当日（与 draft_items 规则一致）',
  lap_no INT NOT NULL,
  turn_seq INT NOT NULL,
  product_cd VARCHAR(64) NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  plating_machine VARCHAR(64) NOT NULL,
  kake DECIMAL(10, 2) NOT NULL DEFAULT 0,
  qty INT NOT NULL DEFAULT 0,
  slots INT NOT NULL DEFAULT 0,
  board_mark VARCHAR(16) NOT NULL DEFAULT 'standard',
  stable_key VARCHAR(128) NULL COMMENT '可选：与③行或客户端枠 id 关联',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_aps_plating_board_draft_lap (draft_id, lap_no, turn_seq),
  KEY idx_aps_plating_board_plan_work (plan_date, work_date),
  KEY idx_aps_plating_board_product (product_cd),
  CONSTRAINT fk_aps_plating_board_cards_draft
    FOREIGN KEY (draft_id) REFERENCES aps_plating_plan_drafts (id)
    ON DELETE CASCADE
);

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 244_standard_costing_tables.sql (original prefix 244)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 標準原価マスタ・月次実績・差異分析（製造原価サイクル）
-- 例: mysql -u USER -p eams_db < backend/database/migrations/244_standard_costing_tables.sql
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 原価標準バージョン（年度・改訂単位）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `cost_standard_versions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `code` varchar(50) NOT NULL COMMENT '表示コード（例 FY2026-A）',
  `fiscal_year` int NOT NULL COMMENT '会計年度',
  `status` varchar(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/active/archived',
  `effective_from` date NOT NULL COMMENT '適用開始日',
  `effective_to` date DEFAULT NULL COMMENT '適用終了日（NULL=無期限）',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_csv_code` (`code`),
  KEY `idx_csv_year_status` (`fiscal_year`, `status`),
  KEY `idx_csv_effective` (`effective_from`, `effective_to`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価バージョン';


-- ---------------------------------------------------------------------------
-- 製品別標準原価ヘッダ（単位当たり）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `product_standard_costs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `version_id` int NOT NULL COMMENT 'cost_standard_versions.id',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '品番',
  `product_name` varchar(200) DEFAULT NULL COMMENT '品名（スナップショット）',
  `material_cost_std` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '直接材料標準（単位）',
  `labor_cost_std` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '直接労務標準（単位）',
  `overhead_cost_std` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '製造間接標準（単位）',
  `total_cost_std` decimal(18,4) NOT NULL DEFAULT 0.0000 COMMENT '標準原価合計（単位）',
  `currency` varchar(10) NOT NULL DEFAULT 'JPY',
  `source` varchar(30) NOT NULL DEFAULT 'manual' COMMENT 'manual/import/rollup',
  `remarks` text,
  `created_by` varchar(100) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_psc_ver_prod` (`version_id`, `product_cd`),
  KEY `idx_psc_product` (`product_cd`),
  CONSTRAINT `fk_psc_version` FOREIGN KEY (`version_id`) REFERENCES `cost_standard_versions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品標準原価ヘッダ';


CREATE TABLE IF NOT EXISTS `product_standard_material_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `header_id` bigint NOT NULL COMMENT 'product_standard_costs.id',
  `line_no` int NOT NULL DEFAULT 1,
  `material_cd` varchar(50) DEFAULT NULL,
  `material_name` varchar(200) DEFAULT NULL,
  `qty_per_unit` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '単位製品当たり数量',
  `scrap_pct` decimal(9,4) NOT NULL DEFAULT 0 COMMENT 'スクラップ率%',
  `standard_unit_price` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '標準単価',
  `amount` decimal(18,4) NOT NULL DEFAULT 0 COMMENT '金額',
  `bom_line_id` int DEFAULT NULL COMMENT '参照BOM行',
  PRIMARY KEY (`id`),
  KEY `idx_psml_header` (`header_id`),
  CONSTRAINT `fk_psml_header` FOREIGN KEY (`header_id`) REFERENCES `product_standard_costs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価 材料明細';


CREATE TABLE IF NOT EXISTS `product_standard_labor_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `header_id` bigint NOT NULL,
  `line_no` int NOT NULL DEFAULT 1,
  `process_cd` varchar(50) DEFAULT NULL,
  `process_name` varchar(200) DEFAULT NULL,
  `std_hours` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '標準直接作業時間',
  `setup_hours` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '段取時間',
  `labor_rate_per_hour` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '標準賃率/時',
  `cost_center_cd` varchar(50) DEFAULT NULL,
  `amount` decimal(18,4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_psll_header` (`header_id`),
  CONSTRAINT `fk_psll_header` FOREIGN KEY (`header_id`) REFERENCES `product_standard_costs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価 労務明細';


CREATE TABLE IF NOT EXISTS `product_standard_overhead_lines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `header_id` bigint NOT NULL,
  `line_no` int NOT NULL DEFAULT 1,
  `cost_center_cd` varchar(50) DEFAULT NULL,
  `allocation_basis` varchar(40) NOT NULL DEFAULT 'machine_hours' COMMENT 'machine_hours/labor_hours/direct_labor_cost',
  `basis_qty_per_unit` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '配賦基準数量/単位',
  `overhead_rate` decimal(18,6) NOT NULL DEFAULT 0 COMMENT '間接費率',
  `amount` decimal(18,4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_psol_header` (`header_id`),
  CONSTRAINT `fk_psol_header` FOREIGN KEY (`header_id`) REFERENCES `product_standard_costs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準原価 間接費明細';


-- ---------------------------------------------------------------------------
-- 会計期間（月次締め単位）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `cost_accounting_periods` (
  `id` int NOT NULL AUTO_INCREMENT,
  `year_month` char(7) NOT NULL COMMENT 'YYYY-MM',
  `status` varchar(20) NOT NULL DEFAULT 'open' COMMENT 'open/closed',
  `notes` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cap_ym` (`year_month`),
  KEY `idx_cap_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='原価会計期間（月次）';


CREATE TABLE IF NOT EXISTS `cost_period_product_costs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `period_id` int NOT NULL,
  `version_id` int DEFAULT NULL COMMENT '標準計算に用いたバージョン（NULL=自動選択）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_name` varchar(200) DEFAULT NULL,
  `finished_good_qty` decimal(18,4) NOT NULL DEFAULT 0 COMMENT '完成品数量',
  `wip_equivalent_qty` decimal(18,4) NOT NULL DEFAULT 0 COMMENT '仕掛約当数量',
  `actual_material_cost` decimal(18,2) DEFAULT NULL COMMENT '実際材料費（当期）',
  `actual_labor_cost` decimal(18,2) DEFAULT NULL COMMENT '実際労務費',
  `actual_overhead_cost` decimal(18,2) DEFAULT NULL COMMENT '実際間接費',
  `standard_material_allowed` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '標準許容 材料',
  `standard_labor_allowed` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '標準許容 労務',
  `standard_overhead_allowed` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '標準許容 間接',
  `variance_material_price` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '材料価格差異',
  `variance_material_qty` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '材料数量差異',
  `variance_labor_rate` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '賃率差異',
  `variance_labor_efficiency` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '作業時間差異',
  `variance_moh_budget` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '間接予算差異',
  `variance_moh_capacity` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '操業度差異',
  `variance_moh_efficiency` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '間接能率差異',
  `remarks` text,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cpp_period_prod` (`period_id`, `product_cd`),
  KEY `idx_cpp_product` (`product_cd`),
  KEY `idx_cpp_version` (`version_id`),
  CONSTRAINT `fk_cpp_period` FOREIGN KEY (`period_id`) REFERENCES `cost_accounting_periods` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cpp_version` FOREIGN KEY (`version_id`) REFERENCES `cost_standard_versions` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='月次品目別 実績・標準許容・差異';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 246_sales_management_tables.sql (original prefix 246)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 販売管理追加テーブル（見積・請求書・与信・契約単価・内示）
-- 例: mysql -u USER -p eams_db < backend/database/migrations/246_sales_management_tables.sql
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 見積テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_quotation` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `quotation_no` varchar(50) NOT NULL COMMENT '見積番号',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `quotation_date` date NOT NULL COMMENT '見積日',
  `valid_until` date DEFAULT NULL COMMENT '有効期限',
  `status` varchar(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/sent/accepted/rejected/expired',
  `subtotal` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '小計',
  `tax_rate` decimal(5,2) NOT NULL DEFAULT 10 COMMENT '税率',
  `tax_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '税額',
  `total_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '合計金額',
  `sales_person` varchar(100) DEFAULT NULL COMMENT '営業担当者',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sq_quotation_no` (`quotation_no`),
  KEY `idx_sq_customer` (`customer_code`),
  KEY `idx_sq_date` (`quotation_date`),
  KEY `idx_sq_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='見積';

-- ---------------------------------------------------------------------------
-- 見積明細テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_quotation_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `quotation_id` int NOT NULL COMMENT 'sales_quotation.id',
  `line_no` int NOT NULL COMMENT '行番号',
  `product_code` varchar(100) NOT NULL COMMENT '品番',
  `product_name` varchar(300) DEFAULT NULL COMMENT '品名',
  `specification` varchar(500) DEFAULT NULL COMMENT '仕様',
  `unit` varchar(20) NOT NULL DEFAULT '個' COMMENT '単位',
  `quantity` int NOT NULL COMMENT '数量',
  `unit_price` decimal(12,2) NOT NULL COMMENT '単価',
  `tax_rate` decimal(5,2) NOT NULL DEFAULT 10 COMMENT '税率',
  `amount` decimal(15,2) NOT NULL COMMENT '金額',
  `remarks` text COMMENT '備考',
  PRIMARY KEY (`id`),
  KEY `idx_sqi_quotation` (`quotation_id`),
  KEY `idx_sqi_product` (`product_code`),
  CONSTRAINT `fk_sqi_quotation` FOREIGN KEY (`quotation_id`) REFERENCES `sales_quotation` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='見積明細';

-- ---------------------------------------------------------------------------
-- 請求書テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_invoice` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `invoice_no` varchar(50) NOT NULL COMMENT '請求書番号',
  `order_id` int DEFAULT NULL COMMENT '受注ID',
  `order_no` varchar(50) DEFAULT NULL COMMENT '受注番号',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `invoice_date` date NOT NULL COMMENT '請求日',
  `due_date` date DEFAULT NULL COMMENT '支払期限',
  `status` varchar(20) NOT NULL DEFAULT 'draft' COMMENT 'draft/issued/paid/overdue/cancelled',
  `subtotal` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '小計',
  `tax_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '税額',
  `total_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '合計金額',
  `paid_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '入金済金額',
  `payment_method` varchar(50) DEFAULT NULL COMMENT '支払方法',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `issued_at` datetime DEFAULT NULL COMMENT '発行日時',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_si_invoice_no` (`invoice_no`),
  KEY `idx_si_order` (`order_id`),
  KEY `idx_si_customer` (`customer_code`),
  KEY `idx_si_date` (`invoice_date`),
  KEY `idx_si_due_date` (`due_date`),
  KEY `idx_si_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='請求書';

-- ---------------------------------------------------------------------------
-- 請求書明細テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_invoice_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `invoice_id` int NOT NULL COMMENT 'sales_invoice.id',
  `line_no` int NOT NULL COMMENT '行番号',
  `product_code` varchar(100) NOT NULL COMMENT '品番',
  `product_name` varchar(300) DEFAULT NULL COMMENT '品名',
  `unit` varchar(20) NOT NULL DEFAULT '個' COMMENT '単位',
  `quantity` int NOT NULL COMMENT '数量',
  `unit_price` decimal(12,2) NOT NULL COMMENT '単価',
  `tax_rate` decimal(5,2) NOT NULL DEFAULT 10 COMMENT '税率',
  `amount` decimal(15,2) NOT NULL COMMENT '金額',
  `remarks` text COMMENT '備考',
  PRIMARY KEY (`id`),
  KEY `idx_sii_invoice` (`invoice_id`),
  KEY `idx_sii_product` (`product_code`),
  CONSTRAINT `fk_sii_invoice` FOREIGN KEY (`invoice_id`) REFERENCES `sales_invoice` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='請求書明細';

-- ---------------------------------------------------------------------------
-- 与信管理テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_credit` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `credit_limit` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '与信限度額',
  `current_balance` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '現在残高',
  `available_credit` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '利用可能額',
  `risk_level` varchar(20) NOT NULL DEFAULT 'low' COMMENT 'low/medium/high/blocked',
  `last_review_date` date DEFAULT NULL COMMENT '前回審査日',
  `next_review_date` date DEFAULT NULL COMMENT '次回審査日',
  `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT 'active/suspended/blocked',
  `remarks` text COMMENT '備考',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sc_customer` (`customer_code`),
  KEY `idx_sc_risk_level` (`risk_level`),
  KEY `idx_sc_status` (`status`),
  KEY `idx_sc_next_review` (`next_review_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='与信管理';

-- ---------------------------------------------------------------------------
-- 契約単価テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_contract_pricing` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `product_code` varchar(100) NOT NULL COMMENT '品番',
  `product_name` varchar(300) DEFAULT NULL COMMENT '品名',
  `contract_price` decimal(12,2) NOT NULL COMMENT '契約単価',
  `standard_price` decimal(12,2) DEFAULT NULL COMMENT '標準単価',
  `discount_rate` decimal(5,2) NOT NULL DEFAULT 0 COMMENT '割引率',
  `valid_from` date NOT NULL COMMENT '適用開始日',
  `valid_until` date DEFAULT NULL COMMENT '適用終了日',
  `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT 'active/expired/cancelled',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_scp_cust_prod_from` (`customer_code`, `product_code`, `valid_from`),
  KEY `idx_scp_customer` (`customer_code`),
  KEY `idx_scp_product` (`product_code`),
  KEY `idx_scp_status` (`status`),
  KEY `idx_scp_valid` (`valid_from`, `valid_until`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='契約単価';

-- ---------------------------------------------------------------------------
-- 内示テーブル
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sales_forecast` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `product_code` varchar(100) NOT NULL COMMENT '品番',
  `product_name` varchar(300) DEFAULT NULL COMMENT '品名',
  `forecast_month` char(7) NOT NULL COMMENT '内示月 (YYYY-MM)',
  `forecast_quantity` int NOT NULL DEFAULT 0 COMMENT '内示数量',
  `confirmed_quantity` int NOT NULL DEFAULT 0 COMMENT '確定数量',
  `status` varchar(20) NOT NULL DEFAULT 'forecast' COMMENT 'forecast/confirmed/revised',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sf_cust_prod_month` (`customer_code`, `product_code`, `forecast_month`),
  KEY `idx_sf_customer` (`customer_code`),
  KEY `idx_sf_product` (`product_code`),
  KEY `idx_sf_month` (`forecast_month`),
  KEY `idx_sf_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内示';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 247_sales_recording.sql (original prefix 247)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 売上計上テーブル（/api/erp/sales/recordings）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `sales_recording` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `recording_no` varchar(50) NOT NULL COMMENT '計上番号',
  `recording_month` varchar(7) NOT NULL COMMENT '計上年月 YYYY-MM',
  `recording_date` date NOT NULL COMMENT '計上日',
  `customer_code` varchar(50) NOT NULL COMMENT '顧客コード',
  `customer_name` varchar(200) DEFAULT NULL COMMENT '顧客名',
  `delivery_id` int DEFAULT NULL COMMENT '出荷ID',
  `delivery_no` varchar(50) DEFAULT NULL COMMENT '出荷番号',
  `order_no` varchar(50) DEFAULT NULL COMMENT '受注番号',
  `product_code` varchar(100) NOT NULL COMMENT '品番',
  `product_name` varchar(300) DEFAULT NULL COMMENT '品名',
  `quantity` int NOT NULL COMMENT '数量',
  `unit_price` decimal(12,2) NOT NULL DEFAULT 0 COMMENT '単価',
  `amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '税抜金額',
  `tax_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '税額',
  `total_amount` decimal(15,2) NOT NULL DEFAULT 0 COMMENT '税込合計',
  `remarks` text COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL COMMENT '作成者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sr_recording_no` (`recording_no`),
  KEY `ix_sr_month` (`recording_month`),
  KEY `ix_sr_customer` (`customer_code`),
  KEY `ix_sr_delivery` (`delivery_id`),
  KEY `ix_sr_date` (`recording_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='売上計上';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 248_ensure_sales_core_tables.sql (original prefix 248)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 販売コアテーブル（受注・出荷）が無い環境向け。003 と同等の IF NOT EXISTS のみ。
-- mysql -u USER -p eams_db < backend/database/migrations/248_ensure_sales_core_tables.sql
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `sales_order` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_no` VARCHAR(50) NOT NULL UNIQUE,
    `customer_code` VARCHAR(50) NOT NULL,
    `customer_name` VARCHAR(200),
    `order_date` DATE NOT NULL,
    `expected_delivery_date` DATE,
    `delivery_address` VARCHAR(500),
    `status` VARCHAR(30) DEFAULT 'draft' COMMENT 'draft,pending,approved,partial_delivered,completed,cancelled',
    `currency` VARCHAR(10) DEFAULT 'JPY',
    `exchange_rate` DECIMAL(10,4) DEFAULT 1,
    `subtotal` DECIMAL(15,2) DEFAULT 0,
    `tax_rate` DECIMAL(5,2) DEFAULT 10,
    `tax_amount` DECIMAL(15,2) DEFAULT 0,
    `discount_rate` DECIMAL(5,2) DEFAULT 0,
    `discount_amount` DECIMAL(15,2) DEFAULT 0,
    `total_amount` DECIMAL(15,2) DEFAULT 0,
    `received_amount` DECIMAL(15,2) DEFAULT 0,
    `payment_status` VARCHAR(20) DEFAULT 'unpaid',
    `payment_term` VARCHAR(100),
    `sales_person` VARCHAR(100),
    `contact_person` VARCHAR(100),
    `contact_phone` VARCHAR(20),
    `remarks` TEXT,
    `created_by` VARCHAR(100),
    `approved_by` VARCHAR(100),
    `approved_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_so_no` (`order_no`),
    INDEX `idx_so_customer` (`customer_code`),
    INDEX `idx_so_date` (`order_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_order_item` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `line_no` INT NOT NULL,
    `product_code` VARCHAR(100) NOT NULL,
    `product_name` VARCHAR(300),
    `specification` VARCHAR(500),
    `unit` VARCHAR(20) DEFAULT '個',
    `quantity` INT NOT NULL,
    `delivered_quantity` INT DEFAULT 0,
    `unit_price` DECIMAL(12,2) NOT NULL,
    `tax_rate` DECIMAL(5,2) DEFAULT 10,
    `tax_amount` DECIMAL(12,2) DEFAULT 0,
    `amount` DECIMAL(15,2) NOT NULL,
    `warehouse_code` VARCHAR(50),
    `expected_delivery_date` DATE,
    `remarks` TEXT,
    FOREIGN KEY (`order_id`) REFERENCES `sales_order`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_delivery` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `delivery_no` VARCHAR(50) NOT NULL UNIQUE,
    `order_id` INT,
    `order_no` VARCHAR(50),
    `customer_code` VARCHAR(50) NOT NULL,
    `customer_name` VARCHAR(200),
    `warehouse_code` VARCHAR(50) NOT NULL,
    `warehouse_name` VARCHAR(200),
    `delivery_date` DATE NOT NULL,
    `delivery_address` VARCHAR(500),
    `status` VARCHAR(20) DEFAULT 'draft' COMMENT 'draft,confirmed,shipped,completed',
    `tracking_no` VARCHAR(100),
    `carrier` VARCHAR(100),
    `total_quantity` INT DEFAULT 0,
    `remarks` TEXT,
    `created_by` VARCHAR(100),
    `confirmed_by` VARCHAR(100),
    `confirmed_at` TIMESTAMP NULL,
    `shipped_at` TIMESTAMP NULL,
    `completed_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_sd_no` (`delivery_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `sales_delivery_item` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `delivery_id` INT NOT NULL,
    `order_item_id` INT,
    `product_code` VARCHAR(100) NOT NULL,
    `product_name` VARCHAR(300),
    `unit` VARCHAR(20) DEFAULT '個',
    `ordered_quantity` INT DEFAULT 0,
    `delivery_quantity` INT NOT NULL,
    `batch_no` VARCHAR(100),
    `remarks` TEXT,
    FOREIGN KEY (`delivery_id`) REFERENCES `sales_delivery`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 249_add_mes_instruction_menus.sql (original prefix 249)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ============================================================
-- Add MES production instruction submenu entries
-- ============================================================

-- Ensure MES production instruction parent exists under MES.
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_PRODUCTION_INSTRUCTION', '生産指示', mes.id, NULL, 'Document', 1
FROM menus mes
WHERE mes.code = 'MES'
LIMIT 1;

-- Ensure cutting instruction menu exists.
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_CUTTING_INSTRUCTION', '切断・面取指示', p.id, '/mes/instruction/cutting', 'Operation', 1
FROM menus p
WHERE p.code = 'MES_PRODUCTION_INSTRUCTION'
LIMIT 1;

-- Ensure forming instruction menu exists (align under parent).
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_FORMING_INSTRUCTION', '成型指示', p.id, '/mes/instruction/forming', 'Document', 2
FROM menus p
WHERE p.code = 'MES_PRODUCTION_INSTRUCTION'
LIMIT 1;

-- Ensure welding instruction menu exists.
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_WELDING_INSTRUCTION', '溶接指示', p.id, '/mes/instruction/welding', 'Connection', 3
FROM menus p
WHERE p.code = 'MES_PRODUCTION_INSTRUCTION'
LIMIT 1;

-- Ensure plating instruction menu exists.
INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MES_PLATING_INSTRUCTION', 'メッキ指示', p.id, '/mes/instruction/plating', 'Operation', 4
FROM menus p
WHERE p.code = 'MES_PRODUCTION_INSTRUCTION'
LIMIT 1;

-- Normalize parent/path/sort/name for MES instruction menus.
UPDATE menus c
JOIN menus p ON p.code = 'MES_PRODUCTION_INSTRUCTION'
SET
  c.parent_id = p.id,
  c.name = CASE c.code
    WHEN 'MES_CUTTING_INSTRUCTION' THEN '切断・面取指示'
    WHEN 'MES_FORMING_INSTRUCTION' THEN '成型指示'
    WHEN 'MES_WELDING_INSTRUCTION' THEN '溶接指示'
    WHEN 'MES_PLATING_INSTRUCTION' THEN 'メッキ指示'
    ELSE c.name
  END,
  c.path = CASE c.code
    WHEN 'MES_CUTTING_INSTRUCTION' THEN '/mes/instruction/cutting'
    WHEN 'MES_FORMING_INSTRUCTION' THEN '/mes/instruction/forming'
    WHEN 'MES_WELDING_INSTRUCTION' THEN '/mes/instruction/welding'
    WHEN 'MES_PLATING_INSTRUCTION' THEN '/mes/instruction/plating'
    ELSE c.path
  END,
  c.sort_order = CASE c.code
    WHEN 'MES_CUTTING_INSTRUCTION' THEN 1
    WHEN 'MES_FORMING_INSTRUCTION' THEN 2
    WHEN 'MES_WELDING_INSTRUCTION' THEN 3
    WHEN 'MES_PLATING_INSTRUCTION' THEN 4
    ELSE c.sort_order
  END
WHERE c.code IN (
  'MES_CUTTING_INSTRUCTION',
  'MES_FORMING_INSTRUCTION',
  'MES_WELDING_INSTRUCTION',
  'MES_PLATING_INSTRUCTION'
);

-- Grant new MES instruction menus to roles that already have MES instruction scope.
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT src.role_id, dst.id
FROM role_menu_permissions src
JOIN menus src_menu ON src_menu.id = src.menu_id
JOIN menus dst ON dst.code IN (
  'MES_CUTTING_INSTRUCTION',
  'MES_WELDING_INSTRUCTION',
  'MES_PLATING_INSTRUCTION'
)
WHERE src_menu.code IN ('MES_PRODUCTION_INSTRUCTION', 'MES_FORMING_INSTRUCTION');

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 250_production_summarys_add_outsourced_warehouse_plan.sql (original prefix 250)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_summarys に外注倉庫計画カラムを追加
ALTER TABLE `production_summarys`
  ADD COLUMN `outsourced_warehouse_plan` int DEFAULT 0 COMMENT '外注倉庫計画' AFTER `outsourced_warehouse_trend`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 251_roller_bom_roller_master.sql (original prefix 251)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ローラーBOM（roller_bom）
-- ローラーマスタ（roller_master）

CREATE TABLE IF NOT EXISTS `roller_bom` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `roller_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ローラー種類',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '設備CD',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_roller_bom_roller_cd` (`roller_cd`),
  KEY `idx_roller_bom_product_cd` (`product_cd`),
  KEY `idx_roller_bom_machine_cd` (`machine_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラーBOM' ROW_FORMAT=Dynamic;

CREATE TABLE IF NOT EXISTS `roller_master` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `roller_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ローラー名',
  `exchange_freq_qty` int NULL DEFAULT NULL COMMENT '交換頻度本数',
  `exchange_freq_month` int NULL DEFAULT NULL COMMENT '交換頻度月',
  `cleaning_freq_month` int NULL DEFAULT NULL COMMENT '清掃頻度月',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '区分',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備CD',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_roller_master_roller_cd` (`roller_cd`),
  KEY `idx_roller_master_machine_cd` (`machine_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラーマスタ' ROW_FORMAT=Dynamic;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 252_roller_usage_status_and_log.sql (original prefix 252)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ローラー使用状況（roller_usage_status）
-- ローラー使用登録（roller_usage_log）

CREATE TABLE IF NOT EXISTS `roller_usage_status` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `roller_type` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT 'ローラー種類',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備CD',
  `machine_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '設備名',
  `exchange_freq_qty` int NULL DEFAULT NULL COMMENT '交換頻度本数',
  `exchange_freq_month` int NULL DEFAULT NULL COMMENT '交換頻度月',
  `cleaning_freq_month` int NULL DEFAULT NULL COMMENT '清掃頻度月',
  `exec_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '実施内容',
  `last_exec_date` date NULL DEFAULT NULL COMMENT '前回実施日',
  `next_exec_date` date NULL DEFAULT NULL COMMENT '次回実施日（予測）',
  `prod_cumulative_qty` int NULL DEFAULT 0 COMMENT '生産累計数（自動）',
  `prod_manual_addon_qty` int NULL DEFAULT 0 COMMENT '手入力補正（自動累計に加算）',
  `planned_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '予定段取品',
  `exchange_remaining_qty` int NULL DEFAULT NULL COMMENT '交換残数',
  `source_roller_master_updated_at` datetime NULL DEFAULT NULL COMMENT 'ローラーマスタ最終同期日時',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_roller_usage_status_roller_cd` (`roller_cd`),
  KEY `idx_roller_usage_status_machine_cd` (`machine_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラー使用状況' ROW_FORMAT=Dynamic;

CREATE TABLE IF NOT EXISTS `roller_usage_log` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `roller_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ローラーCD',
  `exec_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '実施内容',
  `exec_date` date NOT NULL COMMENT '実施日',
  `management_cd` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理CD',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '登録者',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_roller_usage_log_roller_cd` (`roller_cd`),
  KEY `idx_roller_usage_log_exec_date` (`exec_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ローラー使用登録' ROW_FORMAT=Dynamic;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 253_drop_qty_delta_from_roller_usage_log.sql (original prefix 253)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- roller_usage_log から未使用列 qty_delta を削除
ALTER TABLE `roller_usage_log`
  DROP COLUMN `qty_delta`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 254_drop_prod_planned_qty_from_roller_usage_status.sql (original prefix 254)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- roller_usage_status から未使用列 prod_planned_qty（生産予定数）を削除
ALTER TABLE `roller_usage_status`
  DROP COLUMN `prod_planned_qty`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 255_add_prod_manual_addon_qty_to_roller_usage_status.sql (original prefix 255)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ローラー使用状況：単一手入力補正（自動生産累計に加算）
ALTER TABLE `roller_usage_status`
  ADD COLUMN `prod_manual_addon_qty` int NULL DEFAULT 0 COMMENT '手入力補正（自動累計に加算）' AFTER `prod_cumulative_qty`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 256_backfill_molding_actual_plan_from_production_plan_updates_before_20260301.sql (original prefix 256)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- production_plan_updates.quantity を production_summarys.molding_actual_plan へ反映
-- 条件: production_plan_updates.plan_date < '2026-03-01'
-- 紐付け: plan_date = date, product_cd = product_cd

UPDATE `production_summarys` AS ps
INNER JOIN (
  SELECT
    `plan_date`,
    `product_cd`,
    SUM(COALESCE(`quantity`, 0)) AS `quantity_sum`
  FROM `production_plan_updates`
  WHERE `plan_date` < '2026-03-01'
  GROUP BY `plan_date`, `product_cd`
) AS ppu
  ON ppu.`plan_date` = ps.`date`
 AND ppu.`product_cd` = ps.`product_cd`
SET ps.`molding_actual_plan` = ppu.`quantity_sum`
WHERE ps.`date` < '2026-03-01';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 257_unify_forming_instruction_menu.sql (original prefix 257)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- ============================================================
-- Unify MES / ERP 「成型指示」 onto ERP route and single menu entry
-- ============================================================

-- Roles that only had MES forming gain ERP forming menu access.
INSERT IGNORE INTO role_menu_permissions (role_id, menu_id)
SELECT DISTINCT rmp.role_id, erp.id
FROM role_menu_permissions rmp
JOIN menus mes ON mes.id = rmp.menu_id AND mes.code = 'MES_FORMING_INSTRUCTION'
JOIN menus erp ON erp.code = 'ERP_PRODUCTION_INSTR_FORMING';

DELETE rmp FROM role_menu_permissions rmp
JOIN menus m ON m.id = rmp.menu_id AND m.code = 'MES_FORMING_INSTRUCTION';

DELETE FROM menus WHERE code = 'MES_FORMING_INSTRUCTION';

UPDATE menus SET sort_order = 2 WHERE code = 'MES_WELDING_INSTRUCTION';
UPDATE menus SET sort_order = 3 WHERE code = 'MES_PLATING_INSTRUCTION';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 258_add_prod_cumulative_qty_prev_month_end_to_roller_usage_status.sql (original prefix 258)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- roller_usage_status: 前月末までの生産累計（自動再計算用）
ALTER TABLE `roller_usage_status`
  ADD COLUMN `prod_cumulative_qty_prev_month_end` int NULL DEFAULT 0 COMMENT '生産累計数（前月末まで・自動）' AFTER `prod_cumulative_qty`;

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 259_forming_daily_plan_process_run_days.sql (original prefix 259)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 工程別計画試算画面：期間×工程ごとの運行日数
CREATE TABLE IF NOT EXISTS forming_daily_plan_process_run_days (
  id INT AUTO_INCREMENT PRIMARY KEY,
  period_start DATE NOT NULL COMMENT '集計期間開始',
  period_end DATE NOT NULL COMMENT '集計期間終了',
  process_key VARCHAR(32) NOT NULL COMMENT 'cutting|chamfering|molding|plating|welding|inspection',
  run_days INT NOT NULL DEFAULT 0 COMMENT '運行日数',
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_period_process (period_start, period_end, process_key),
  KEY idx_period (period_start, period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別計画試算・工程別運行日';

-- >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
-- merged from 260_forming_daily_plan_process_run_calendar.sql (original prefix 260)
-- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

-- 工程別運行日：工程×日历日的勾选（稀疏存储）；meta 区分「从未保存」与「已保存（含全日未勾选）」
DROP TABLE IF EXISTS forming_daily_plan_process_run_days;

CREATE TABLE IF NOT EXISTS forming_daily_plan_process_run_calendar_meta (
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (period_start, period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別運行日カレンダー保存済みフラグ';

CREATE TABLE IF NOT EXISTS forming_daily_plan_process_run_calendar (
  id INT AUTO_INCREMENT PRIMARY KEY,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  process_key VARCHAR(32) NOT NULL COMMENT 'cutting|chamfering|molding|plating|welding|inspection',
  calendar_date DATE NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_period_process_cal (period_start, period_end, process_key, calendar_date),
  KEY idx_period (period_start, period_end),
  KEY idx_process (process_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工程別運行日（チェックされた日のみ保持）';
