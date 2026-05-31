-- 受注番号ルール: 納入先+受注日+納期でヘッダー番号、明細は製品別サブ番号
SET NAMES utf8mb4;

SET @col_dest := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order' AND COLUMN_NAME = 'destination_cd'
);
SET @ddl_dest := IF(
  @col_dest = 0,
  'ALTER TABLE sales_order ADD COLUMN destination_cd VARCHAR(50) NULL COMMENT ''納入先CD'' AFTER customer_name',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_dest;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_item_no := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order_item' AND COLUMN_NAME = 'item_order_no'
);
SET @ddl_item_no := IF(
  @col_item_no = 0,
  'ALTER TABLE sales_order_item ADD COLUMN item_order_no VARCHAR(100) NULL COMMENT ''製品別受注番号（親受注番号-品番）'' AFTER line_no',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_item_no;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_so_ref := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order' AND COLUMN_NAME = 'source_ref'
);
SET @ddl_so_ref := IF(
  @col_so_ref > 0,
  'ALTER TABLE sales_order MODIFY COLUMN source_ref VARCHAR(120) NULL COMMENT ''同期キー OD|納入先CD|受注日|納期''',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_so_ref;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_order_no := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'sales_order' AND COLUMN_NAME = 'order_no'
);
SET @ddl_order_no := IF(
  @col_order_no > 0,
  'ALTER TABLE sales_order MODIFY COLUMN order_no VARCHAR(50) NOT NULL COMMENT ''受注番号（納入先-受注日-納期）''',
  'SELECT 1'
);
PREPARE stmt FROM @ddl_order_no;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
