-- Smart-EMAP データベース初期化スクリプト
-- 作成日時: 2026年1月7日（日本時間）

-- データベースの文字セット設定
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- タイムゾーンを日本時間に設定
SET time_zone = '+09:00';

-- データベースが存在しない場合は作成
-- 注意: データベース名は環境変数 DB_NAME に合わせて変更してください
CREATE DATABASE IF NOT EXISTS eams_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE eams_db;

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ユーザーID（主キー）',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT 'ユーザー名（ログインID、一意制約）',
    email VARCHAR(100) UNIQUE NOT NULL COMMENT 'メールアドレス（一意制約）',
    hashed_password VARCHAR(255) NOT NULL COMMENT 'ハッシュ化されたパスワード',
    full_name VARCHAR(100) COMMENT '氏名（フルネーム）',
    role VARCHAR(20) DEFAULT 'user' COMMENT 'ユーザーロール（user:一般ユーザー、admin:管理者）',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'アカウント有効フラグ（TRUE:有効、FALSE:無効）',
    last_login_token VARCHAR(500) NULL COMMENT '最後にログインしたデバイスのトークン（単一デバイスログイン用）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_username (username) COMMENT 'ユーザー名インデックス',
    INDEX idx_email (email) COMMENT 'メールアドレスインデックス'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザーマスターテーブル';

-- 顧客マスター
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_code VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_code (customer_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 仕入先マスター
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_supplier_code (supplier_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 製品マスター
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    specification TEXT,
    unit VARCHAR(20),
    standard_price DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_product_code (product_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 材料マスター
CREATE TABLE IF NOT EXISTS materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_code VARCHAR(50) UNIQUE NOT NULL,
    material_name VARCHAR(200) NOT NULL,
    specification TEXT,
    unit VARCHAR(20),
    standard_price DECIMAL(15, 2),
    safety_stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_material_code (material_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 設備マスター
CREATE TABLE IF NOT EXISTS equipment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_code VARCHAR(50) UNIQUE NOT NULL,
    equipment_name VARCHAR(200) NOT NULL,
    equipment_type VARCHAR(50),
    capacity DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_equipment_code (equipment_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 工程マスター
CREATE TABLE IF NOT EXISTS processes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    process_code VARCHAR(50) UNIQUE NOT NULL,
    process_name VARCHAR(200) NOT NULL,
    description TEXT,
    standard_time INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_process_code (process_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 受注テーブル
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    delivery_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    INDEX idx_order_number (order_number),
    INDEX idx_order_date (order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 在庫テーブル
CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_type VARCHAR(20) NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    location VARCHAR(100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_item (item_type, item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 生産計画テーブル
CREATE TABLE IF NOT EXISTS production_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_number VARCHAR(50) UNIQUE NOT NULL,
    product_id INT NOT NULL,
    planned_quantity INT NOT NULL,
    plan_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_plan_number (plan_number),
    INDEX idx_plan_date (plan_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 製造実績テーブル
CREATE TABLE IF NOT EXISTS production_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    record_number VARCHAR(50) UNIQUE NOT NULL,
    product_id INT NOT NULL,
    equipment_id INT,
    quantity INT NOT NULL,
    good_quantity INT,
    defect_quantity INT,
    production_date DATE NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    INDEX idx_record_number (record_number),
    INDEX idx_production_date (production_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初期データの挿入
INSERT INTO users (username, email, hashed_password, full_name, role) VALUES
('zkily', 'chougai@arais.co.jp', '$2b$12$ox/KTAkwcVvNNXnZ1aBaUOTdleC6kckSVVTllfFjlab2l0OpVBfXC', '管理者', 'admin');

-- 完了メッセージ
SELECT '✅ Smart-EMAP データベース初期化完了' AS message;

