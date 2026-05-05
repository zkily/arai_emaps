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
