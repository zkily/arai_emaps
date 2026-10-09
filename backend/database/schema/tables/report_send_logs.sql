-- TABLE: report_send_logs
-- 生成元: scripts/export_schema_split.py
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `report_send_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `report_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'レポートコード',
  `trigger_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'manual' COMMENT 'manual|scheduled',
  `reference_key` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '参照キー（重複送信防止）',
  `parameters` json DEFAULT NULL COMMENT '実行パラメータのスナップショット',
  `file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '添付ファイル名',
  `file_size` int DEFAULT NULL COMMENT '添付ファイルサイズ（byte）',
  `recipient_count` int NOT NULL DEFAULT '0' COMMENT '送信対象件数',
  `success_count` int NOT NULL DEFAULT '0' COMMENT '送信成功件数',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'success|partial|failed',
  `message` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '結果メッセージ',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'エラー内容',
  `triggered_by` int DEFAULT NULL COMMENT '実行者 users.id（手動時）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  KEY `idx_report_send_logs_code_ref` (`report_code`,`reference_key`),
  KEY `idx_report_send_logs_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='レポート送信履歴';

SET FOREIGN_KEY_CHECKS = 1;
