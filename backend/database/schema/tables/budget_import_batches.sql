-- TABLE: budget_import_batches
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `budget_import_batches` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) NOT NULL COMMENT 'アップロードファイル名',
  `months_json` text COMMENT '取込対象年月 JSON 例: year/month 配列',
  `total_rows` int NOT NULL DEFAULT '0' COMMENT 'CSV行数（品番行）',
  `matched_rows` int NOT NULL DEFAULT '0' COMMENT '製品マスタ紐付成功行数',
  `unmatched_rows` int NOT NULL DEFAULT '0' COMMENT '紐付失敗行数',
  `inserted_rows` int NOT NULL DEFAULT '0' COMMENT '新規挿入セル数（年月×品番）',
  `updated_rows` int NOT NULL DEFAULT '0' COMMENT '上書き更新セル数',
  `uploaded_by` varchar(100) DEFAULT NULL,
  `remark` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_budget_import_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='予算CSV取込バッチ';

SET FOREIGN_KEY_CHECKS = 1;
