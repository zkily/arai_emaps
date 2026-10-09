-- TABLE: supply_part_transactions
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `supply_part_transactions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `stock_id` bigint NOT NULL COMMENT '在庫カードID',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品番',
  `txn_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'transfer_in/manual_in/production_in/shipment_out/adjust',
  `quantity` int NOT NULL DEFAULT '0' COMMENT '数量（入庫プラス、出庫マイナス）',
  `balance_after` int NOT NULL DEFAULT '0' COMMENT '発生後残高',
  `occurred_date` date NOT NULL COMMENT '発生日',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `created_by_user_id` int DEFAULT NULL COMMENT '登録者ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_supply_txn_stock` (`stock_id`),
  KEY `idx_supply_txn_product` (`product_cd`),
  KEY `idx_supply_txn_date` (`occurred_date`),
  CONSTRAINT `fk_supply_txn_stock` FOREIGN KEY (`stock_id`) REFERENCES `supply_part_stocks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='補給品入出庫明細';

SET FOREIGN_KEY_CHECKS = 1;
