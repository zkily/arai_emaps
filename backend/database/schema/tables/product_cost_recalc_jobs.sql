-- TABLE: product_cost_recalc_jobs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `product_cost_recalc_jobs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'queued' COMMENT 'queued/running/completed/failed/partial',
  `mode` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'append_snapshot' COMMENT 'append_snapshot / replace_current',
  `scope` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT 'selected' COMMENT 'selected / all',
  `total_items` int NOT NULL DEFAULT '0',
  `done_items` int NOT NULL DEFAULT '0',
  `success_items` int NOT NULL DEFAULT '0',
  `failed_items` int NOT NULL DEFAULT '0',
  `payload_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '入力（製品リスト等）JSON',
  `error_log` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '失敗明細JSON（配列）',
  `result_snapshot_ids_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '生成スナップショットIDリストJSON',
  `message` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '進捗/エラー概要',
  `created_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `started_at` datetime DEFAULT NULL,
  `finished_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pcrj_status` (`status`),
  KEY `idx_pcrj_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='累計単価 一括再計算ジョブ';

SET FOREIGN_KEY_CHECKS = 1;
