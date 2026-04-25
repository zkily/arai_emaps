SET NAMES utf8mb4;

CREATE TABLE `backup_history`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ファイル名',
  `file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ファイルパス',
  `file_size` bigint NULL DEFAULT NULL COMMENT 'ファイルサイズ（バイト）',
  `backup_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'auto' COMMENT 'タイプ（auto/manual）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'completed' COMMENT 'ステータス（completed/failed）',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'エラーメッセージ',
  `started_at` datetime NULL DEFAULT NULL COMMENT '開始日時',
  `completed_at` datetime NULL DEFAULT NULL COMMENT '完了日時',
  `created_by` int NULL DEFAULT NULL COMMENT '作成者（手動の場合）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_backup_history_type`(`backup_type` ASC) USING BTREE,
  INDEX `idx_backup_history_status`(`status` ASC) USING BTREE,
  INDEX `idx_backup_history_created`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'バックアップ履歴テーブル' ROW_FORMAT = Dynamic;
INSERT INTO `backup_history` VALUES (1, 'backup_20260416_140559.sql.gz', '\\backup\\backup_20260416_140559.sql.gz', NULL, 'manual', 'failed', '[WinError 2] 指定されたファイルが見つかりません。', '2026-04-16 14:05:59', '2026-04-16 14:05:59', 2, '2026-04-16 14:05:59');
INSERT INTO `backup_history` VALUES (2, 'backup_20260416_141146.sql.gz', '\\backup\\backup_20260416_141146.sql.gz', 44454554, 'manual', 'completed', NULL, '2026-04-16 14:11:46', '2026-04-16 14:11:56', 2, '2026-04-16 14:11:46');
INSERT INTO `backup_history` VALUES (3, 'backup_20260416_142435.sql.gz', '\\\\192.168.1.200\\社内共有\\02_生産管理部\\バックアップ\\backup_20260416_142435.sql.gz', 44454889, 'manual', 'completed', NULL, '2026-04-16 14:24:35', '2026-04-16 14:24:49', 2, '2026-04-16 14:24:35');
