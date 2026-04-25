SET NAMES utf8mb4;

CREATE TABLE `outsourcing_material_issues`  (
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
