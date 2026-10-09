-- TABLE: product_cost_cumulative_snapshots
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_cost_cumulative_snapshots` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `snapshot_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '同一スナップショットのグループID（UUID）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品CD',
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートCD',
  `bom_header_id` int DEFAULT NULL COMMENT 'スナップショット時のBOMヘッダID',
  `row_kind` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'route_step' COMMENT 'route_step / unassigned',
  `row_order` int NOT NULL DEFAULT '0' COMMENT '表示順（stepソート＋unassignedは最後）',
  `step_no` int DEFAULT NULL COMMENT 'ルートstep_no（unassignedはNULL）',
  `process_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '工程CD',
  `stage_label` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '表示用ラベル（〜 xx 工程完了時点）',
  `material_increment` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '材料単価（当段）',
  `part_increment` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '部品単価（当段）',
  `process_increment` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '工程単価（当段）',
  `stage_increment` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '当段増分',
  `cumulative_unit_price` decimal(18,2) NOT NULL DEFAULT '0.00' COMMENT '累計単価',
  `currency` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'JPY',
  `is_latest` tinyint(1) NOT NULL DEFAULT '0' COMMENT '同一 product+route の最新フラグ',
  `source_job_id` bigint DEFAULT NULL COMMENT '生成元ジョブID',
  `remarks` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_pcs_group` (`snapshot_id`),
  KEY `idx_pcs_pr` (`product_cd`,`route_cd`),
  KEY `idx_pcs_latest` (`product_cd`,`route_cd`,`is_latest`),
  KEY `idx_pcs_created` (`product_cd`,`route_cd`,`created_at`),
  KEY `idx_pcs_job` (`source_job_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品×ルート 累計単価スナップショット';

SET FOREIGN_KEY_CHECKS = 1;
