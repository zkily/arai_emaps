-- TABLE: production_equipment_capacity_item
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_equipment_capacity_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `capacity_id` int NOT NULL COMMENT '設備能力ID',
  `line_no` int NOT NULL DEFAULT '0' COMMENT '行番',
  `part_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '部品番号',
  `part_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '部品名',
  `customer_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '取引先名',
  `survey_target` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '調査対象',
  `monthly_qty` decimal(14,2) NOT NULL DEFAULT '0.00' COMMENT '設定数 個/月',
  `qty_days` decimal(6,2) NOT NULL DEFAULT '0.00' COMMENT '設定数に対する稼働日数',
  `ct_sec` decimal(10,3) NOT NULL DEFAULT '0.000' COMMENT 'CT 秒/個',
  `availability_rate` decimal(6,4) NOT NULL DEFAULT '0.9000' COMMENT '可動率 0-1',
  `first_pass_rate` decimal(6,4) NOT NULL DEFAULT '0.9900' COMMENT '直行率 0-1',
  `cavity_count` decimal(8,2) NOT NULL DEFAULT '1.00' COMMENT '取り数',
  `setup_hours` decimal(8,3) NOT NULL DEFAULT '0.000' COMMENT '段取り h/回',
  `actual_days` decimal(6,2) NOT NULL DEFAULT '0.00' COMMENT '実生産日数',
  `reference_rate` decimal(10,2) DEFAULT NULL COMMENT '参照能率 本/H',
  `current_rate` decimal(10,2) DEFAULT NULL COMMENT '現在能率 本/H',
  `takt1_date` date DEFAULT NULL COMMENT 'タクト1 日付',
  `takt1_ct` decimal(10,3) DEFAULT NULL COMMENT 'タクト1 実測CT秒',
  `takt1_inspect` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'タクト1 検査',
  `takt1_prep` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'タクト1 準備',
  `takt1_overall` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'タクト1 総合',
  `takt2_date` date DEFAULT NULL COMMENT 'タクト2 日付',
  `takt2_ct` decimal(10,3) DEFAULT NULL COMMENT 'タクト2 実測CT秒',
  `takt2_inspect` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'タクト2 検査',
  `takt2_prep` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'タクト2 準備',
  `takt2_overall` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'タクト2 総合',
  `remarks` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備考',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_peci_capacity` (`capacity_id`),
  CONSTRAINT `fk_peci_capacity` FOREIGN KEY (`capacity_id`) REFERENCES `production_equipment_capacity` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='生産設備能力 品目';

SET FOREIGN_KEY_CHECKS = 1;
