-- 部品マスタ（外購部品・子assemblyの標準単価・通貨・為替）
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `part_masters` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `part_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '部品CD（BOMの子品目CDと同一可）',
  `part_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '部品名',
  `uom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '個' COMMENT '単位',
  `unit_price` decimal(18,6) NOT NULL DEFAULT 0.000000 COMMENT '単価（原通貨）',
  `currency` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'JPY' COMMENT '通貨コード',
  `exchange_rate` decimal(18,6) NOT NULL DEFAULT 1.000000 COMMENT '基準通貨JPY換算：1原通貨当たり円（JPY時は1）',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '主仕入先CD',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'active' COMMENT 'active/inactive',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_part_masters_cd` (`part_cd`),
  KEY `idx_part_masters_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='部品マスタ';
