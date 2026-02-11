-- 在庫受払履歴 (stock_transaction_logs)
DROP TABLE IF EXISTS `stock_transaction_logs`;

CREATE TABLE `stock_transaction_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '在庫操作履歴ID (BIGINT推奨)',
  `stock_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '在庫種別 (製品,材料,部品,仕掛品)',
  `transaction_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '操作種別 (入庫,出庫,実績、不良、廃棄、保留、調整、初期)',
  `target_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '品目コード',
  `location_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '保管場所コード',
  `lot_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'ロット番号 (重要)',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '工程コード',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '設備コード',
  `quantity` decimal(18, 4) NOT NULL COMMENT '操作数量 (増減符号付き推奨: 入庫+10, 出庫-10)',
  `unit` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '単位 (kg, pcs, m)',
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '関連伝票No (受注No, 発注No, 製造指図No)',
  `related_log_id` bigint NULL DEFAULT NULL COMMENT '取消時の元ログIDなど',
  `operator_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '操作担当者ID',
  `operator_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '担当者名(ログとして名前も残すのはアリ)',
  `transaction_time` datetime(3) NOT NULL COMMENT '操作日時 (ミリ秒まで記録推奨)',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
  `source_file` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '来源文件名',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '備考',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_target_time`(`target_cd` ASC, `transaction_time` ASC) USING BTREE,
  INDEX `idx_location_target`(`location_cd` ASC, `target_cd` ASC) USING BTREE,
  INDEX `idx_lot`(`lot_no` ASC, `target_cd` ASC) USING BTREE,
  INDEX `idx_order`(`order_no` ASC) USING BTREE,
  INDEX `idx_source_file`(`source_file` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 119 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '在庫受払履歴' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
