-- TABLE: stock_transaction_logs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `stock_transaction_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '在庫操作履歴ID (BIGINT推奨)',
  `stock_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '在庫種別 (製品,材料,部品,仕掛品)',
  `transaction_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '操作種別 (入庫,出庫,実績、不良、廃棄、保留、調整、初期)',
  `target_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '品目コード',
  `location_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '保管場所コード',
  `lot_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT 'ロット番号 (重要)',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '工程コード',
  `machine_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '設備コード',
  `quantity` decimal(18,4) NOT NULL COMMENT '操作数量 (増減符号付き推奨: 入庫+10, 出庫-10)',
  `defect_qty` int DEFAULT NULL COMMENT '任意。成型不良集計は transaction_type=不良 の quantity を使用',
  `unit` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '単位 (kg, pcs, m)',
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '関連伝票No (受注No, 発注No, 製造指図No)',
  `notes` varchar(100) DEFAULT NULL COMMENT '注文番号等（トリガー互換・削除照合用）',
  `related_log_id` bigint DEFAULT NULL COMMENT '取消時の元ログIDなど',
  `operator_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '操作担当者ID',
  `operator_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '担当者名(ログとして名前も残すのはアリ)',
  `transaction_time` datetime(3) NOT NULL COMMENT '操作日時 (ミリ秒まで記録推奨)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
  `source_file` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '来源文件名',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT '備考',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_target_time` (`target_cd`,`transaction_time`) USING BTREE,
  KEY `idx_location_target` (`location_cd`,`target_cd`) USING BTREE,
  KEY `idx_lot` (`lot_no`,`target_cd`) USING BTREE,
  KEY `idx_order` (`order_no`) USING BTREE,
  KEY `idx_source_file` (`source_file`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC COMMENT='在庫受払履歴';

SET FOREIGN_KEY_CHECKS = 1;
