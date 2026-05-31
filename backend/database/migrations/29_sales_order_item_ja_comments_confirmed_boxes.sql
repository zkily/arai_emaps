-- sales_order_item: 日本語コメント整備 + 確定箱数カラム
SET NAMES utf8mb4;

ALTER TABLE sales_order_item COMMENT = '受注明細（販売受注の行）';

-- 確定箱数（order_daily 同期用）
SET @col_boxes := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order_item' AND COLUMN_NAME = 'confirmed_boxes'
);
SET @ddl_boxes := IF(
  @col_boxes = 0,
  'ALTER TABLE sales_order_item ADD COLUMN confirmed_boxes INT NOT NULL DEFAULT 0 COMMENT ''確定箱数（order_daily.confirmed_boxes）'' AFTER quantity',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_boxes;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 既存カラムの日本語コメント
ALTER TABLE sales_order_item
  MODIFY COLUMN id INT AUTO_INCREMENT COMMENT '受注明細ID',
  MODIFY COLUMN order_id INT NOT NULL COMMENT '受注ID（sales_order.id）',
  MODIFY COLUMN line_no INT NOT NULL COMMENT '行番号',
  MODIFY COLUMN product_code VARCHAR(100) NOT NULL COMMENT '品番',
  MODIFY COLUMN product_name VARCHAR(300) NULL COMMENT '品名',
  MODIFY COLUMN specification VARCHAR(500) NULL COMMENT '仕様',
  MODIFY COLUMN unit VARCHAR(20) DEFAULT '個' COMMENT '単位',
  MODIFY COLUMN quantity INT NOT NULL COMMENT '受注数量（本数）',
  MODIFY COLUMN unit_price DECIMAL(12,2) NOT NULL COMMENT '単価',
  MODIFY COLUMN delivered_quantity INT DEFAULT 0 COMMENT '出荷済数量',
  MODIFY COLUMN tax_rate DECIMAL(5,2) DEFAULT 10 COMMENT '税率（%）',
  MODIFY COLUMN tax_amount DECIMAL(12,2) DEFAULT 0 COMMENT '税額',
  MODIFY COLUMN amount DECIMAL(15,2) NOT NULL COMMENT '金額',
  MODIFY COLUMN warehouse_code VARCHAR(50) NULL COMMENT '倉庫コード',
  MODIFY COLUMN expected_delivery_date DATE NULL COMMENT '出荷予定日',
  MODIFY COLUMN remarks TEXT NULL COMMENT '備考';

-- confirmed_boxes（追加済みの場合もコメントを付与）
SET @col_boxes2 := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order_item' AND COLUMN_NAME = 'confirmed_boxes'
);
SET @ddl_boxes2 := IF(
  @col_boxes2 > 0,
  'ALTER TABLE sales_order_item MODIFY COLUMN confirmed_boxes INT NOT NULL DEFAULT 0 COMMENT ''確定箱数（order_daily.confirmed_boxes）''',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_boxes2;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- source_order_daily_id（28 適用済み環境）
SET @col_od := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order_item' AND COLUMN_NAME = 'source_order_daily_id'
);
SET @ddl_od := IF(
  @col_od > 0,
  'ALTER TABLE sales_order_item MODIFY COLUMN source_order_daily_id INT NULL COMMENT ''同期元日別受注ID（order_daily.id）''',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_od;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
