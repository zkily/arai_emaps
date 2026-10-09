-- TABLE: aps_plating_plan_board_date_memos
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `aps_plating_plan_board_date_memos` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `draft_id` int NOT NULL COMMENT '親ドラフトID（aps_plating_plan_drafts.id）',
  `lap_work_date` date NOT NULL COMMENT '日付行のカレンダー日',
  `memo` text NOT NULL COMMENT '日付行メモ本文（空文字はアプリ側で保存）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_aps_plating_board_date_memo` (`draft_id`,`lap_work_date`),
  KEY `idx_aps_plating_board_date_memo_draft` (`draft_id`),
  CONSTRAINT `fk_aps_plating_board_date_memo_draft` FOREIGN KEY (`draft_id`) REFERENCES `aps_plating_plan_drafts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='メッキ投入ボード日付行メモ';

SET FOREIGN_KEY_CHECKS = 1;
