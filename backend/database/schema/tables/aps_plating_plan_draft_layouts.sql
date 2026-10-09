-- TABLE: aps_plating_plan_draft_layouts
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `aps_plating_plan_draft_layouts` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `draft_id` int NOT NULL COMMENT '親ドラフトID（aps_plating_plan_drafts.id）',
  `block_seq` int NOT NULL DEFAULT '0' COMMENT 'ブロック並び順（追加レイアウト追加順・0 起点）',
  `plan_date` date NOT NULL COMMENT 'このブロックの計画日（lap_work_date のベース日付）',
  `start_time` varchar(5) NOT NULL DEFAULT '08:00' COMMENT 'このブロックの開始時刻（HH:mm）',
  `minutes_per_lap` int NOT NULL DEFAULT '100' COMMENT '1 周の所要分（メッキ周期）',
  `jigs_per_lap` int NOT NULL DEFAULT '100' COMMENT '1 周の治具本数（ボード全体で揃える）',
  `lap_count` int NOT NULL DEFAULT '1' COMMENT 'このブロックの周目数',
  `base_lap_no` int NOT NULL DEFAULT '1' COMMENT 'グローバル周目番号の起点（このブロックの最初の周目）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_aps_plating_layouts_draft_seq` (`draft_id`,`block_seq`),
  KEY `idx_aps_plating_layouts_plan_date` (`plan_date`),
  KEY `idx_aps_plating_layouts_draft_plan` (`draft_id`,`plan_date`),
  CONSTRAINT `fk_aps_plating_layouts_draft` FOREIGN KEY (`draft_id`) REFERENCES `aps_plating_plan_drafts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='メッキ計画 追加レイアウトブロック（カード未配置でも基本骨格を永続化）';

SET FOREIGN_KEY_CHECKS = 1;
