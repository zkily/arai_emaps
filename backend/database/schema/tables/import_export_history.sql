-- TABLE: import_export_history
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `import_export_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '種類（import/export）',
  `master_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'マスター種類',
  `filename` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ファイル名',
  `file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'ファイルパス',
  `format` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'フォーマット（csv/xlsx）',
  `encoding` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文字コード',
  `total_records` int DEFAULT '0' COMMENT '総件数',
  `success_records` int DEFAULT '0' COMMENT '成功件数',
  `error_records` int DEFAULT '0' COMMENT 'エラー件数',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'processing' COMMENT 'ステータス（processing/success/partial_error/failed）',
  `error_details` json DEFAULT NULL COMMENT 'エラー詳細',
  `options` json DEFAULT NULL COMMENT 'オプション（update_existing等）',
  `user_id` int DEFAULT NULL COMMENT '実行ユーザーID',
  `started_at` datetime DEFAULT NULL COMMENT '開始日時',
  `completed_at` datetime DEFAULT NULL COMMENT '完了日時',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_import_export_type` (`type`),
  KEY `idx_import_export_master` (`master_type`),
  KEY `idx_import_export_status` (`status`),
  KEY `idx_import_export_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='インポート/エクスポート履歴テーブル';

SET FOREIGN_KEY_CHECKS = 1;
