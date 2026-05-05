SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for shipping_warehouse_daily_stock
-- ----------------------------
DROP TABLE IF EXISTS `shipping_warehouse_daily_stock`;
CREATE TABLE `shipping_warehouse_daily_stock`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '納入先CD',
  `work_date` date NOT NULL COMMENT '日付',
  `weekday` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '曜日',
  `order_qty` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '受注数',
  `forecast_qty` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '内示数',
  `warehouse_carryover` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '倉庫繰越',
  `warehouse_actual` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '倉庫実績',
  `warehouse_defect` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '倉庫不良',
  `warehouse_disposal` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '倉庫廃棄',
  `warehouse_hold` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '倉庫保留品',
  `warehouse_stock` decimal(18, 2) NOT NULL DEFAULT 0.00 COMMENT '倉庫在庫',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_shipping_warehouse_daily_stock`(`destination_cd` ASC, `product_cd` ASC, `work_date` ASC) USING BTREE,
  INDEX `idx_shipping_warehouse_daily_stock_work_date`(`work_date` ASC) USING BTREE,
  INDEX `idx_shipping_warehouse_daily_stock_product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_shipping_warehouse_daily_stock_destination_cd`(`destination_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '倉庫日次在庫' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of shipping_warehouse_daily_stock
-- ----------------------------

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
