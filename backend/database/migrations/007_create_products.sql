SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for products
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '製品ID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD（ユニークな製品コード）',
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品名称',
  `product_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '製品種別（例：量産品 / 試作品）',
  `location_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '製品倉庫' COMMENT '保管場所CD',
  `start_use_date` date NULL DEFAULT NULL COMMENT '使用開始日',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'カテゴリ（例：センサー、ケースなど）',
  `department_id` int NULL DEFAULT NULL COMMENT '所属部門ID（外部キー）',
  `delivery_destination_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '納入先CD（外部キー）',
  `process_count` int NULL DEFAULT 1 COMMENT '工程数（標準の製造工程数）',
  `lead_time` int NULL DEFAULT NULL COMMENT 'リードタイム（日数）',
  `lot_size` int NULL DEFAULT 1 COMMENT 'ロットサイズ（まとめて作る単位）',
  `is_multistage` tinyint(1) NULL DEFAULT 1 COMMENT '多段階工程フラグ（TRUE=多段階）',
  `priority` int NULL DEFAULT 2 COMMENT '製品の優先度（1=高, 2=中, 3=低）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT 'ステータス（active / inactive）',
  `part_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '部品番号（部品連携時の識別子）',
  `vehicle_model` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '対応車種',
  `box_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '梱包タイプ（例：段ボール、プラ箱）',
  `unit_per_box` int NULL DEFAULT NULL COMMENT '1箱あたりの入数',
  `dimensions` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'サイズ（例：100x200x300）',
  `weight` decimal(10, 2) NULL DEFAULT NULL COMMENT '重量（kg 単位）',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '使用材料CD（外部キー）',
  `cut_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '切断長さ（mm）',
  `chamfer_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '面取り長さ（mm）',
  `developed_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '展開長さ（mm）',
  `take_count` int NULL DEFAULT NULL COMMENT '取り数（1材料あたりの取り個数）',
  `scrap_length` decimal(10, 2) NULL DEFAULT NULL COMMENT '端材長さ（mm）',
  `bom_id` int NULL DEFAULT NULL COMMENT 'BOM ID（構成マスタ参照）',
  `route_cd` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '工程ルートID（外部キー）',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '備考欄',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `safety_days` int NULL DEFAULT NULL COMMENT '安全在庫日数',
  `unit_price` decimal(10, 2) NULL DEFAULT NULL COMMENT '販売単価',
  `product_alias` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '別名',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `product_cd`(`product_cd` ASC) USING BTREE,
  INDEX `idx_location_cd`(`location_cd` ASC) USING BTREE,
  INDEX `idx_start_use_date`(`start_use_date` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '製品マスタ（拡張版）' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
