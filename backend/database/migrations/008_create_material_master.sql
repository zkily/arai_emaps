SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for materials
-- ----------------------------
DROP TABLE IF EXISTS `material_master`;
DROP TABLE IF EXISTS `materials`;
CREATE TABLE `materials` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '材料ID',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '材料CD',
  `material_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '材料名',
  `material_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '材料種類',
  `standard_spec` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '規格',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '単位（kg / 本 / m など）',
  `diameter` decimal(10, 2) NULL DEFAULT NULL COMMENT '直径（mm）',
  `thickness` decimal(10, 2) NULL DEFAULT NULL COMMENT '厚さ（mm）',
  `length` decimal(10, 2) NULL DEFAULT NULL COMMENT '長さ（mm）',
  `supply_classification` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '支給区分（社内 / 支給）',
  `pieces_per_bundle` int NULL DEFAULT NULL COMMENT '束本数',
  `usegae` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用途',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '仕入先CD（外部キー）',
  `unit_price` decimal(10, 2) NULL DEFAULT NULL COMMENT '単重単価（円/kg 等）',
  `long_weight` decimal(10, 2) NULL DEFAULT NULL COMMENT '長尺単重（kg/本）',
  `single_price` decimal(10, 2) NULL DEFAULT NULL COMMENT '一本単価（円）',
  `safety_stock` int NULL DEFAULT 0 COMMENT '安全在庫（単位数）',
  `lead_time` int NULL DEFAULT NULL COMMENT 'リードタイム（日）',
  `storage_location` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '保管場所',
  `status` tinyint NULL DEFAULT 1 COMMENT '状態（1=有効, 0=無効）',
  `tolerance_range` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '公差範囲',
  `tolerance_1` decimal(10, 3) NULL DEFAULT NULL COMMENT '公差１',
  `tolerance_2` decimal(10, 3) NULL DEFAULT NULL COMMENT '公差２',
  `range_value` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '範囲',
  `min_value` decimal(10, 2) NULL DEFAULT NULL COMMENT '最小値',
  `max_value` decimal(10, 2) NULL DEFAULT NULL COMMENT '最大値',
  `actual_value_1` decimal(10, 3) NULL DEFAULT NULL COMMENT '実力値１',
  `actual_value_2` decimal(10, 3) NULL DEFAULT NULL COMMENT '実力値２',
  `actual_value_3` decimal(10, 3) NULL DEFAULT NULL COMMENT '実力値３',
  `representative_model` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '代表品種',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`, `material_cd`) USING BTREE,
  UNIQUE INDEX `material_cd`(`material_cd` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '材料マスタ' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
