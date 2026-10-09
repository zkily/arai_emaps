-- TABLE: chamfering_plans
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `chamfering_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `cutting_management_id` int DEFAULT NULL COMMENT '元切断指示ID（新規追加時はNULL）',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_day` date NOT NULL COMMENT '生産日',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `production_order` int DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `actual_production_quantity` int DEFAULT '0' COMMENT '生産数',
  `production_lot_size` int DEFAULT NULL COMMENT 'ロット数',
  `lot_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ロットNo',
  `cutting_length` decimal(10,2) DEFAULT NULL COMMENT '切断長',
  `chamfering_length` decimal(10,2) DEFAULT NULL COMMENT '面取長',
  `developed_length` decimal(10,2) DEFAULT NULL COMMENT '展開長',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '原材料',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '管理コード',
  `cd` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'CD（管理コード後5位）',
  `production_completed` tinyint DEFAULT NULL COMMENT '生産完了',
  `no_count` tinyint DEFAULT NULL COMMENT 'カウント無',
  `has_sw_process` tinyint DEFAULT NULL COMMENT 'SW工程',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_cutting_management_id` (`cutting_management_id`),
  KEY `idx_production_month` (`production_month`),
  KEY `idx_production_day` (`production_day`),
  KEY `idx_production_line` (`production_line`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='面取バッチ一覧（chamfering_plans）';

SET FOREIGN_KEY_CHECKS = 1;
