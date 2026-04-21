-- 製品×ルート 累計単価スナップショット / 一括再計算ジョブ
-- 適用場面：全新庫 / 老庫升級（幂等）
--
-- 【必須】本ファイルを接続先 DB（例: eams_db）で実行しないと、
--   `product_cost_cumulative_snapshots` 不存在 (1146) となり API が失敗します。
--   例: mysql -u USER -p eams_db < backend/database/migrations/230_product_cost_cumulative_snapshots.sql
SET NAMES utf8mb4;

-- ---------------------------------------------------------------------------
-- 累計単価スナップショット（画面「単価累計（工程完了時点）」の行を保存）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `product_cost_cumulative_snapshots` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `snapshot_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '同一スナップショットのグループID（UUID）',
  `product_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '製品CD',
  `route_cd` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT 'ルートCD',
  `bom_header_id` int DEFAULT NULL COMMENT 'スナップショット時のBOMヘッダID',
  `row_kind` varchar(20) NOT NULL DEFAULT 'route_step' COMMENT 'route_step / unassigned',
  `row_order` int NOT NULL DEFAULT 0 COMMENT '表示順（stepソート＋unassignedは最後）',
  `step_no` int DEFAULT NULL COMMENT 'ルートstep_no（unassignedはNULL）',
  `process_cd` varchar(50) DEFAULT NULL COMMENT '工程CD',
  `stage_label` varchar(200) DEFAULT NULL COMMENT '表示用ラベル（〜 xx 工程完了時点）',
  `material_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '材料単価（当段）',
  `part_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '部品単価（当段）',
  `process_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '工程単価（当段）',
  `stage_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '当段増分',
  `cumulative_unit_price` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '累計単価',
  `currency` varchar(10) NOT NULL DEFAULT 'JPY',
  `is_latest` tinyint(1) NOT NULL DEFAULT 0 COMMENT '同一 product+route の最新フラグ',
  `source_job_id` bigint DEFAULT NULL COMMENT '生成元ジョブID',
  `remarks` text,
  `created_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_pcs_group` (`snapshot_id`),
  KEY `idx_pcs_pr` (`product_cd`, `route_cd`),
  KEY `idx_pcs_latest` (`product_cd`, `route_cd`, `is_latest`),
  KEY `idx_pcs_created` (`product_cd`, `route_cd`, `created_at`),
  KEY `idx_pcs_job` (`source_job_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='製品×ルート 累計単価スナップショット';


-- ---------------------------------------------------------------------------
-- 一括再計算ジョブ（非同期）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `product_cost_recalc_jobs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `status` varchar(20) NOT NULL DEFAULT 'queued' COMMENT 'queued/running/completed/failed/partial',
  `mode` varchar(30) NOT NULL DEFAULT 'append_snapshot' COMMENT 'append_snapshot / replace_current',
  `scope` varchar(30) NOT NULL DEFAULT 'selected' COMMENT 'selected / all',
  `total_items` int NOT NULL DEFAULT 0,
  `done_items` int NOT NULL DEFAULT 0,
  `success_items` int NOT NULL DEFAULT 0,
  `failed_items` int NOT NULL DEFAULT 0,
  `payload_json` longtext COMMENT '入力（製品リスト等）JSON',
  `error_log` longtext COMMENT '失敗明細JSON（配列）',
  `result_snapshot_ids_json` longtext COMMENT '生成スナップショットIDリストJSON',
  `message` varchar(500) DEFAULT NULL COMMENT '進捗/エラー概要',
  `created_by` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `started_at` datetime DEFAULT NULL,
  `finished_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_pcrj_status` (`status`),
  KEY `idx_pcrj_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='累計単価 一括再計算ジョブ';

-- 既に decimal(18,6) で `product_cost_cumulative_snapshots` を作成済みの場合のみ、
-- 次を対象 DB で実行して金額列を 2 桁に揃える（新規作成は上記 CREATE でそのまま 18,2）。
-- ALTER TABLE `product_cost_cumulative_snapshots`
--   MODIFY `material_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '材料単価（当段）',
--   MODIFY `part_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '部品単価（当段）',
--   MODIFY `process_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '工程単価（当段）',
--   MODIFY `stage_increment` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '当段増分',
--   MODIFY `cumulative_unit_price` decimal(18,2) NOT NULL DEFAULT 0 COMMENT '累計単価';
