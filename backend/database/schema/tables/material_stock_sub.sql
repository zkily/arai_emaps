-- TABLE: material_stock_sub
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `material_stock_sub` (
  `id` int NOT NULL AUTO_INCREMENT,
  `material_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料CD',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '材料名',
  `date` date NOT NULL COMMENT '日期',
  `current_stock` decimal(10,2) DEFAULT '0.00' COMMENT '現在在庫',
  `safety_stock` decimal(10,2) DEFAULT '0.00' COMMENT '安全在庫',
  `max_stock` decimal(10,2) DEFAULT '0.00' COMMENT '最大在庫',
  `unit` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '単位',
  `unit_price` decimal(10,2) DEFAULT '0.00' COMMENT '単価',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '仕入先CD',
  `supplier_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '仕入先名',
  `lead_time` int DEFAULT '0' COMMENT 'リードタイム',
  `planned_usage` decimal(10,2) DEFAULT '0.00' COMMENT '計画使用数',
  `order_quantity` decimal(10,2) DEFAULT '0.00' COMMENT '注文束数',
  `order_bundle_quantity` decimal(10,2) DEFAULT '0.00' COMMENT '注文本数',
  `bundle_weight` decimal(10,2) DEFAULT '0.00' COMMENT '捆重量',
  `order_amount` decimal(15,2) DEFAULT '0.00' COMMENT '注文金額',
  `standard_spec` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '規格',
  `pieces_per_bundle` int DEFAULT '0' COMMENT '每捆件数',
  `long_weight` decimal(10,2) DEFAULT '0.00' COMMENT '长重量',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '備考',
  `label_color` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ラベル色（白/緑）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最終更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_material_cd_date` (`material_cd`,`date`),
  KEY `idx_date` (`date`),
  KEY `idx_supplier_cd` (`supplier_cd`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='材料在庫サブ（手動注文データ）';

SET FOREIGN_KEY_CHECKS = 1;
