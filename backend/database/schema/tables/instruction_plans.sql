-- TABLE: instruction_plans
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `instruction_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `production_month` date NOT NULL COMMENT '生産月',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン',
  `priority_order` int DEFAULT NULL COMMENT '順位',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `planned_quantity` int DEFAULT '0' COMMENT '計画数',
  `start_date` datetime DEFAULT NULL COMMENT '開始期日',
  `end_date` datetime DEFAULT NULL COMMENT '終了期日',
  `production_lot_size` int DEFAULT NULL COMMENT '生産ロット数',
  `lot_number` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ロットNo.',
  `is_cutting_instructed` tinyint(1) DEFAULT '0' COMMENT '切断指示（チェック）',
  `has_chamfering_process` tinyint(1) DEFAULT '0' COMMENT '面取工程（チェック）',
  `is_chamfering_instructed` tinyint(1) DEFAULT '0' COMMENT '面取指示（チェック）',
  `has_sw_process` tinyint(1) DEFAULT '0' COMMENT 'SW工程（チェック）',
  `is_sw_instructed` tinyint(1) DEFAULT '0' COMMENT 'SW指示（チェック）',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '管理コード',
  `actual_production_quantity` int DEFAULT '0' COMMENT '生産数',
  `take_count` int DEFAULT NULL COMMENT '取数',
  `cutting_length` decimal(10,2) DEFAULT NULL COMMENT '切断長',
  `chamfering_length` decimal(10,2) DEFAULT NULL COMMENT '面取長',
  `developed_length` decimal(10,2) DEFAULT NULL COMMENT '展開長',
  `scrap_length` decimal(10,2) DEFAULT NULL COMMENT '端材長さ（mm）',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '原材料',
  `material_manufacturer` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '材料メーカー',
  `standard_specification` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '規格',
  `use_material_stock_sub` tinyint(1) NOT NULL DEFAULT '0' COMMENT '使用サブ在庫（0=反映対象, 1=対象外・material_stock_subで手動）',
  `usage_count` decimal(10,4) NOT NULL DEFAULT '1.0000' COMMENT '材料使用数（1=1本, <1=他行と同一本を按分）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `aps_batch_plan_id` int DEFAULT NULL COMMENT 'APS 批次計画（aps_batch_plans.id）参照',
  `release_cancelled_at` datetime DEFAULT NULL COMMENT '上游指示撤回日時',
  `release_cancel_reason` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '上游指示撤回理由',
  `release_cancel_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '上游指示撤回者',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_production_month` (`production_month`) USING BTREE,
  KEY `idx_product_code` (`product_cd`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='切断指示計画';

SET FOREIGN_KEY_CHECKS = 1;
