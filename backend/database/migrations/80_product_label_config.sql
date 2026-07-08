-- 製品ラベル（現品票）設定マスタ
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `product_label_config` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `product_cd` VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '製品CD',
  `label_product_name` VARCHAR(100) NULL COMMENT '加工用/现场製品名',
  `process_unit_qty` INT NULL COMMENT '加工入数（非 unit_per_box）',
  `process_slot_1` VARCHAR(50) NULL COMMENT '成型后工程名槽位1',
  `process_slot_2` VARCHAR(50) NULL,
  `process_slot_3` VARCHAR(50) NULL,
  `process_slot_4` VARCHAR(50) NULL,
  `process_slot_5` VARCHAR(50) NULL,
  `process_slot_6` VARCHAR(50) NULL,
  `process_slot_7` VARCHAR(50) NULL,
  `process_slot_8` VARCHAR(50) NULL,
  `paper_color` VARCHAR(30) NULL COMMENT '印刷用纸颜色',
  `product_name_color` VARCHAR(20) NULL COMMENT '製品名打印色',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_product_label_config_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='製品ラベル（現品票）設定';
