-- TABLE: aps_plating_plan_board_cards
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `aps_plating_plan_board_cards` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主キー',
  `draft_id` int NOT NULL COMMENT '親ドラフトID（aps_plating_plan_drafts.id）',
  `draft_version_no` int NOT NULL DEFAULT '1' COMMENT '保存時草稿バージョン（主表 version_no のスナップショット）',
  `lap_work_date` date NOT NULL COMMENT '当該周目のカレンダー日（表示期間・週次スケジュール用）',
  `lap_start_time` varchar(5) DEFAULT NULL COMMENT '当該周目開始時刻（HH:mm）',
  `lap_end_time` varchar(5) DEFAULT NULL COMMENT '当該周目終了時刻（HH:mm）',
  `lap_no` int NOT NULL COMMENT '周目番号（ボード段番号・永続 lap_no）',
  `turn_seq` int NOT NULL COMMENT '週目内並び順（列への割当順）',
  `product_cd` varchar(64) NOT NULL COMMENT '製品コード',
  `product_name` varchar(255) NOT NULL COMMENT '製品名',
  `plating_machine` varchar(64) NOT NULL COMMENT 'メッキ治具（設備名）',
  `kake` decimal(10,2) NOT NULL DEFAULT '0.00' COMMENT '掛け数（生産効率・1枠換算）',
  `qty` int NOT NULL DEFAULT '0' COMMENT '割当数量',
  `slots` int NOT NULL DEFAULT '0' COMMENT '枠数（治具本数換算）',
  `board_mark` varchar(16) NOT NULL DEFAULT 'standard' COMMENT 'ボードマーク（standard／manual／rush）',
  `stable_key` varchar(128) DEFAULT NULL COMMENT '安定キー（③明細・クライアント枠 id との紐付け）',
  `until_depleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '数量非表示（無くなり次第）；合計には実数を加算',
  `text_red` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'ボード上の製品名・数量を赤字で強調表示',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  KEY `idx_aps_plating_board_draft_lap` (`draft_id`,`lap_no`,`turn_seq`),
  KEY `idx_aps_plating_board_product` (`product_cd`),
  KEY `idx_aps_plating_board_draft_lap_date` (`draft_id`,`lap_work_date`,`lap_no`,`turn_seq`),
  CONSTRAINT `fk_aps_plating_board_cards_draft` FOREIGN KEY (`draft_id`) REFERENCES `aps_plating_plan_drafts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='メッキ投入スケジュールボード枠（1治具枠＝1行・周目 lap_no／順 turn_seq）';

SET FOREIGN_KEY_CHECKS = 1;
