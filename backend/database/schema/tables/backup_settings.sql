-- TABLE: backup_settings
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `backup_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `auto_backup_enabled` tinyint(1) DEFAULT '0' COMMENT '自動バックアップ有効',
  `schedule` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'daily' COMMENT 'スケジュール（daily/weekly/monthly）',
  `schedule_time` time DEFAULT '02:00:00' COMMENT '実行時刻',
  `storage_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '/backup/' COMMENT '保存先パス',
  `retention_count` int DEFAULT '7' COMMENT '保持世代数',
  `include_files` tinyint(1) DEFAULT '0' COMMENT 'ファイルも含める',
  `compression_enabled` tinyint(1) DEFAULT '1' COMMENT '圧縮有効',
  `encryption_enabled` tinyint(1) DEFAULT '0' COMMENT '暗号化有効',
  `notify_on_complete` tinyint(1) DEFAULT '0' COMMENT '完了時通知',
  `notify_on_error` tinyint(1) DEFAULT '1' COMMENT 'エラー時通知',
  `updated_by` int DEFAULT NULL COMMENT '更新者',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='バックアップ設定テーブル';

SET FOREIGN_KEY_CHECKS = 1;
