-- TABLE: production_schedules
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `production_schedules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `line_id` int NOT NULL COMMENT '産線ID',
  `order_no` int DEFAULT NULL COMMENT '順番',
  `order_id` int DEFAULT NULL COMMENT '外部注文ID',
  `item_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '品名',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製品コード',
  `material_shortage` tinyint(1) NOT NULL DEFAULT '0' COMMENT '材料不足フラグ',
  `lot_qty` int NOT NULL DEFAULT '0' COMMENT '実績生ロット数',
  `planned_process_qty` int NOT NULL COMMENT '予定加工数量',
  `prev_month_carryover` int NOT NULL DEFAULT '0' COMMENT '前月繰越',
  `due_date` date DEFAULT NULL COMMENT '完成期日',
  `material_date` date DEFAULT NULL COMMENT '材料調達日',
  `forced_start_date` date DEFAULT NULL COMMENT '排産開始日の強制下限（NULL=未指定）',
  `setup_time` int NOT NULL DEFAULT '0' COMMENT '段取時間（分）',
  `efficiency` decimal(5,2) NOT NULL DEFAULT '100.00' COMMENT '時間能率（%）',
  `daily_capacity` int NOT NULL COMMENT '日生産能力',
  `planned_output_qty` int NOT NULL DEFAULT '0' COMMENT '予定産出数量',
  `start_date` date DEFAULT NULL COMMENT '開始期日',
  `end_date` date DEFAULT NULL COMMENT '終了期日',
  `completion_rate` decimal(5,2) DEFAULT NULL COMMENT '完成比率（%）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PLANNING' COMMENT 'PLANNING / IN_PROGRESS / COMPLETED',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `planned_batch_count` int NOT NULL DEFAULT '0',
  `lot_size_snapshot` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_ps_line` (`line_id`),
  KEY `idx_ps_status` (`status`),
  KEY `idx_ps_product_cd` (`product_cd`),
  CONSTRAINT `fk_ps_machine` FOREIGN KEY (`line_id`) REFERENCES `machines` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排産工単主計画表';

SET FOREIGN_KEY_CHECKS = 1;
