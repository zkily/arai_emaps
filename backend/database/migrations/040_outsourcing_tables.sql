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
