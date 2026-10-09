-- TABLE: kanban_issuance
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `kanban_issuance` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `process_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工程（cutting=切断 / chamfering=面取）',
  `source_id` int NOT NULL COMMENT '元指示ID（cutting_management.id または chamfering_management.id）',
  `kanban_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'カンバン番号',
  `issue_date` date DEFAULT NULL COMMENT '発行日',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '状態（pending=待発行 / issued=発行済 / completed=完了）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製品名',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ライン',
  `cutting_machine` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '切断機',
  `material_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '原材料',
  `standard_specification` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '規格',
  `management_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '管理コード',
  `start_date` date DEFAULT NULL COMMENT '成型期間（開始）',
  `end_date` date DEFAULT NULL COMMENT '成型期間（終了）',
  `planned_quantity` int DEFAULT NULL COMMENT '計画数（成型計画数）',
  `production_lot_size` int DEFAULT NULL COMMENT '生産ロット数（成型ロット）',
  `actual_production_quantity` int DEFAULT NULL COMMENT '生産数（ロット本数）',
  `take_count` int DEFAULT NULL COMMENT '取数',
  `cutting_length` decimal(10,2) DEFAULT NULL COMMENT '切断長',
  `chamfering_length` decimal(10,2) DEFAULT NULL COMMENT '面取長',
  `developed_length` decimal(10,2) DEFAULT NULL COMMENT '展開長',
  `has_chamfering_process` tinyint(1) DEFAULT '0' COMMENT '面取工程あり',
  `is_first_product` tinyint(1) DEFAULT '0' COMMENT '初（初回生産マーク）',
  `lot_number` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ロットNo.',
  `production_day` date DEFAULT NULL COMMENT '生産日',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_process_type` (`process_type`),
  KEY `idx_source_id` (`source_id`),
  KEY `idx_issue_date` (`issue_date`),
  KEY `idx_kanban_no` (`kanban_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='カンバン発行';

SET FOREIGN_KEY_CHECKS = 1;
