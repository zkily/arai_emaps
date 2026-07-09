-- 製品用ラベル設定マスタ
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `product_use_label_config` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `product_cd` VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `use_label_product_name` VARCHAR(100) NULL COMMENT '製品用製品名',
  `unit_qty` INT NULL COMMENT '入数',
  `part_no` VARCHAR(80) NULL COMMENT '品番',
  `destination_name` VARCHAR(200) NULL COMMENT '納入先名',
  `paper_color` VARCHAR(30) NULL COMMENT '用紙色',
  `product_name_color` VARCHAR(20) NULL COMMENT '製品名色',
  `back_no_1` VARCHAR(50) NULL COMMENT '背番号1',
  `back_no_2` VARCHAR(50) NULL COMMENT '背番号2',
  `back_no_3` VARCHAR(50) NULL COMMENT '背番号3',
  `barcode_no` VARCHAR(80) NULL COMMENT 'バーコード番号',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_product_use_label_config_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='製品用ラベル設定';

INSERT IGNORE INTO menus (code, name, parent_id, path, icon, sort_order)
SELECT 'MASTER_PRODUCT_USE_LABEL_CONFIG', '製品用ラベル設定', m.id, '/master/product-use-label-config', 'Tickets', 2
FROM menus m
WHERE m.code = 'MASTER_LABEL'
LIMIT 1;
