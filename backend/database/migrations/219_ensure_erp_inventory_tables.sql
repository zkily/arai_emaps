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
