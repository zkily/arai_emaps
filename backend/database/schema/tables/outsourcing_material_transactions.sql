-- TABLE: outsourcing_material_transactions
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `outsourcing_material_transactions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '取引ID',
  `transaction_date` date NOT NULL COMMENT '取引日',
  `transaction_type` enum('issue','usage','return') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '取引種別（支給/使用/返却）',
  `supplier_cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '外注先コード',
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料コード',
  `material_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '材料名',
  `related_no` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '関連番号',
  `quantity` decimal(12,3) NOT NULL COMMENT '数量',
  `stock_after` decimal(12,3) DEFAULT NULL COMMENT '取引後在庫',
  `operator` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '担当者',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_transaction_date` (`transaction_date`) USING BTREE,
  KEY `idx_transaction_type` (`transaction_type`) USING BTREE,
  KEY `idx_supplier_cd` (`supplier_cd`) USING BTREE,
  KEY `idx_material_cd` (`material_cd`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='支給材料入出庫履歴';

SET FOREIGN_KEY_CHECKS = 1;
