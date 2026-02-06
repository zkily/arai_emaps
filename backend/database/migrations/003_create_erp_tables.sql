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
