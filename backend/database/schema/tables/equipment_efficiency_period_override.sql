-- TABLE: equipment_efficiency_period_override
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `equipment_efficiency_period_override` (
  `id` int NOT NULL AUTO_INCREMENT,
  `machine_cd` varchar(50) NOT NULL COMMENT '設備CD',
  `machines_name` varchar(100) DEFAULT NULL COMMENT '設備名（表示用）',
  `product_cd` varchar(50) NOT NULL COMMENT '製品CD',
  `product_name` varchar(100) DEFAULT NULL COMMENT '製品名（表示用）',
  `efficiency_rate` decimal(10,1) NOT NULL COMMENT '能率（本/H）',
  `period_from` date NOT NULL COMMENT '適用開始日（含む）',
  `period_to` date NOT NULL COMMENT '適用終了日（含む）',
  `status` int DEFAULT '1' COMMENT '1=有効 0=無効',
  `remarks` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ee_period_ov_machine` (`machine_cd`),
  KEY `idx_ee_period_ov_product` (`product_cd`),
  KEY `idx_ee_period_ov_period` (`machine_cd`,`product_cd`,`period_from`,`period_to`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='設備能率の期間指定（製品+設備+期間）';

SET FOREIGN_KEY_CHECKS = 1;
