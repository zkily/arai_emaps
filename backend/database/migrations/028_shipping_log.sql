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
