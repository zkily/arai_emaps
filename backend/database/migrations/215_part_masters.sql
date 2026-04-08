-- 部品マスタ（外購部品・子assemblyの標準単価・通貨・為替）— テーブル名 parts
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `parts` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `part_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '部品CD（BOMの子品目CDと同一可）',
  `part_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '部品名',
  `category` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '分类',
  `kind` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'N' COMMENT '種別 T/N/F',
  `settlement_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '有償支給' COMMENT '決済種類',
  `uom` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '個' COMMENT '単位',
  `unit_price` decimal(18,6) NOT NULL DEFAULT 0.000000 COMMENT '単価（原通貨）',
  `material_unit_price` decimal(18,6) NOT NULL DEFAULT 0.000000 COMMENT '部品材料単価（原通貨）',
  `total_unit_price` decimal(18,6) GENERATED ALWAYS AS (`unit_price` + `material_unit_price`) STORED COMMENT '総単価（単価+部品材料単価）',
  `currency` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'JPY' COMMENT '通貨コード',
  `exchange_rate` decimal(18,6) NOT NULL DEFAULT 1.000000 COMMENT '基準通貨JPY換算：1原通貨当たり円（JPY時は1）',
  `supplier_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '主仕入先CD',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '1=有効 0=無効',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '備考',
  `created_by` varchar(100) DEFAULT NULL,
  `updated_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_parts_part_cd` (`part_cd`),
  KEY `idx_parts_status` (`status`),
  KEY `idx_parts_kind` (`kind`),
  KEY `idx_parts_settlement_type` (`settlement_type`),
  CONSTRAINT `chk_parts_kind` CHECK (`kind` IN ('T','N','F')),
  CONSTRAINT `chk_parts_settlement_type` CHECK (`settlement_type` IN ('有償支給','無償支給','自給','その他'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='部品マスタ';
