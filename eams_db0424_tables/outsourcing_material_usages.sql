SET NAMES utf8mb4;

CREATE TABLE `outsourcing_material_usages`  (
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
