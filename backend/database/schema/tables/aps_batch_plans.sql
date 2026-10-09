-- TABLE: aps_batch_plans
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `aps_batch_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'システムID',
  `aps_schedule_id` int NOT NULL COMMENT 'APS production_schedules.id',
  `production_month` date NOT NULL COMMENT '生産月（YYYY-MM-01）',
  `production_line` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ライン（管理コード用：下2桁が重要）',
  `priority_order` int DEFAULT NULL COMMENT '順位（APS order_no）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品CD',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '製品名',
  `planned_quantity` int NOT NULL DEFAULT '0' COMMENT 'このバッチで計画する本数',
  `upstream_defect_qty` int NOT NULL DEFAULT '0' COMMENT '前工程不良合計（cutting_management + chamfering_management、management_code 照合）',
  `original_planned_quantity` int DEFAULT NULL COMMENT '計画一覧確定時のロット本数（生産進捗の計画数表示用）',
  `production_lot_size` int NOT NULL DEFAULT '0' COMMENT '総バッチ数（= lotサイズ/批次数の上限）',
  `lot_number` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ロットNo（1..N）',
  `start_date` datetime DEFAULT NULL COMMENT '開始日時（時間別ガント由来）',
  `end_date` datetime DEFAULT NULL COMMENT '終了日時（時間別ガント由来）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PLANNED' COMMENT '状態',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_aps_schedule_id_lot_number` (`aps_schedule_id`,`lot_number`) USING BTREE,
  KEY `idx_aps_schedule_id` (`aps_schedule_id`),
  KEY `idx_production_month` (`production_month`),
  KEY `idx_product_cd` (`product_cd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='APS バッチ計画';

SET FOREIGN_KEY_CHECKS = 1;
