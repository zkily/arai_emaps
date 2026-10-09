-- TABLE: product_bom_headers
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_bom_headers` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `parent_product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '親製品CD',
  `bom_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'production' COMMENT 'BOM種別 (engineering/production)',
  `revision` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '1' COMMENT '版番',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'active' COMMENT '状態 (active/historical)',
  `effective_from` date DEFAULT NULL COMMENT '有効開始日',
  `effective_to` date DEFAULT NULL COMMENT '有効終了日 (NULL=無期限)',
  `base_quantity` decimal(12,4) NOT NULL DEFAULT '1.0000' COMMENT '基準数量',
  `uom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '個' COMMENT '単位',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '備考',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '作成者',
  `updated_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '更新者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_bom_hdr_parent` (`parent_product_cd`),
  KEY `idx_bom_hdr_effective` (`parent_product_cd`,`bom_type`,`effective_from`,`effective_to`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='明細BOMヘッダ';

SET FOREIGN_KEY_CHECKS = 1;
