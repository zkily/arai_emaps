-- ================================================================
-- 出荷管理：倉庫日次在庫テーブル作成
-- Version: 235
-- ================================================================

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `shipping_warehouse_daily_stock` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `product_cd` VARCHAR(50) NOT NULL COMMENT '製品CD',
  `product_name` VARCHAR(255) NOT NULL COMMENT '製品名',
  `destination_cd` VARCHAR(50) NOT NULL COMMENT '納入先CD',
  `work_date` DATE NOT NULL COMMENT '日付',
  `weekday` VARCHAR(10) NOT NULL COMMENT '曜日',
  `order_qty` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '受注数',
  `forecast_qty` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '内示数',
  `warehouse_carryover` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫繰越',
  `warehouse_actual` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫実績',
  `warehouse_defect` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫不良',
  `warehouse_disposal` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫廃棄',
  `warehouse_hold` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫保留品',
  `warehouse_stock` DECIMAL(18,2) NOT NULL DEFAULT 0 COMMENT '倉庫在庫',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_shipping_warehouse_daily_stock` (`destination_cd`, `product_cd`, `work_date`),
  KEY `idx_shipping_warehouse_daily_stock_work_date` (`work_date`),
  KEY `idx_shipping_warehouse_daily_stock_product_cd` (`product_cd`),
  KEY `idx_shipping_warehouse_daily_stock_destination_cd` (`destination_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='倉庫日次在庫';
