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
