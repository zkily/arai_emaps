-- TABLE: backup_history
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `backup_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ファイル名',
  `file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ファイルパス',
  `file_size` bigint DEFAULT NULL COMMENT 'ファイルサイズ（バイト）',
  `backup_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'auto' COMMENT 'タイプ（auto/manual）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'completed' COMMENT 'ステータス（completed/failed）',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'エラーメッセージ',
  `started_at` datetime DEFAULT NULL COMMENT '開始日時',
  `completed_at` datetime DEFAULT NULL COMMENT '完了日時',
  `created_by` int DEFAULT NULL COMMENT '作成者（手動の場合）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_backup_history_type` (`backup_type`),
  KEY `idx_backup_history_status` (`status`),
  KEY `idx_backup_history_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='バックアップ履歴テーブル';

SET FOREIGN_KEY_CHECKS = 1;
