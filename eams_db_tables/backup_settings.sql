SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Table structure for backup_settings
-- ----------------------------
DROP TABLE IF EXISTS `backup_settings`;
CREATE TABLE `backup_settings`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `auto_backup_enabled` tinyint(1) NULL DEFAULT 0 COMMENT '自動バックアップ有効',
  `schedule` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'daily' COMMENT 'スケジュール（daily/weekly/monthly）',
  `schedule_time` time NULL DEFAULT '02:00:00' COMMENT '実行時刻',
  `storage_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '/backup/' COMMENT '保存先パス',
  `retention_count` int NULL DEFAULT 7 COMMENT '保持世代数',
  `include_files` tinyint(1) NULL DEFAULT 0 COMMENT 'ファイルも含める',
  `compression_enabled` tinyint(1) NULL DEFAULT 1 COMMENT '圧縮有効',
  `encryption_enabled` tinyint(1) NULL DEFAULT 0 COMMENT '暗号化有効',
  `notify_on_complete` tinyint(1) NULL DEFAULT 0 COMMENT '完了時通知',
  `notify_on_error` tinyint(1) NULL DEFAULT 1 COMMENT 'エラー時通知',
  `updated_by` int NULL DEFAULT NULL COMMENT '更新者',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'バックアップ設定テーブル' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of backup_settings
-- ----------------------------
INSERT INTO `backup_settings` VALUES (1, 1, 'daily', '02:00:00', '\\\\192.168.1.200\\社内共有\\02_生産管理部\\バックアップ', 7, 0, 1, 0, 0, 1, 2, '2026-04-16 19:57:08');

-- ----------------------------
SET FOREIGN_KEY_CHECKS = 1;
