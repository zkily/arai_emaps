-- SEED: backup_settings
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

INSERT IGNORE INTO `backup_settings` (`id`, `auto_backup_enabled`, `schedule`, `schedule_time`, `storage_path`, `retention_count`, `include_files`, `compression_enabled`, `encryption_enabled`, `notify_on_complete`, `notify_on_error`, `updated_by`) VALUES
(1, 1, 'daily', '02:00:00', '/backup/', 7, 0, 1, 0, 0, 1, NULL);

SET FOREIGN_KEY_CHECKS = 1;
