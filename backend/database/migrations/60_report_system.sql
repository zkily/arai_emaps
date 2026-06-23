-- レポート配信システム（報告定義・スケジュール・送信履歴 + 通知イベント）
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 報告定義（報告タイプの登録表）
CREATE TABLE IF NOT EXISTS `report_definitions` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `report_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'レポートコード',
  `report_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'レポート名',
  `category` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'MES' COMMENT 'MES|ERP|APS',
  `default_format` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'xlsx' COMMENT 'xlsx|pdf|both',
  `parameter_schema` json NULL COMMENT 'パラメータスキーマ（UI 描画用）',
  `event_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '紐づく通知イベントコード',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '説明',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_report_definitions_code` (`report_code`),
  INDEX `idx_report_definitions_event` (`event_code`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'レポート定義' ROW_FORMAT = Dynamic;

-- 報告スケジュール（定時自動配信設定）
CREATE TABLE IF NOT EXISTS `report_schedules` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `report_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'レポートコード',
  `schedule_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'daily' COMMENT 'daily|weekly|monthly',
  `schedule_time` time NOT NULL DEFAULT '08:00:00' COMMENT '実行時刻（JST）',
  `schedule_config` json NULL COMMENT '曜日・実行日などの詳細',
  `parameters` json NULL COMMENT '既定パラメータ（相対日付表現を含む）',
  `format` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '出力形式の上書き',
  `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
  `last_run_at` datetime NULL DEFAULT NULL COMMENT '最終実行日時',
  `next_run_at` datetime NULL DEFAULT NULL COMMENT '次回実行予定',
  `created_by` int NULL DEFAULT NULL COMMENT '作成者 users.id',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  PRIMARY KEY (`id`),
  INDEX `idx_report_schedules_code` (`report_code`),
  INDEX `idx_report_schedules_active` (`is_active`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'レポートスケジュール' ROW_FORMAT = Dynamic;

-- 報告送信履歴（レポート単位の監査ログ）
CREATE TABLE IF NOT EXISTS `report_send_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `report_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'レポートコード',
  `trigger_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'manual' COMMENT 'manual|scheduled',
  `reference_key` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '参照キー（重複送信防止）',
  `parameters` json NULL COMMENT '実行パラメータのスナップショット',
  `file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '添付ファイル名',
  `file_size` int NULL DEFAULT NULL COMMENT '添付ファイルサイズ（byte）',
  `recipient_count` int NOT NULL DEFAULT 0 COMMENT '送信対象件数',
  `success_count` int NOT NULL DEFAULT 0 COMMENT '送信成功件数',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'success|partial|failed',
  `message` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '結果メッセージ',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'エラー内容',
  `triggered_by` int NULL DEFAULT NULL COMMENT '実行者 users.id（手動時）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  PRIMARY KEY (`id`),
  INDEX `idx_report_send_logs_code_ref` (`report_code`, `reference_key`),
  INDEX `idx_report_send_logs_created` (`created_at`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'レポート送信履歴' ROW_FORMAT = Dynamic;

-- 通知イベント（受信者・SMTP/LINE は通知センターで共通管理）
INSERT INTO notification_settings (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled, is_active)
VALUES
('REPORT_CUTTING_DAILY_ACTUAL', '切断工程実績レポート', '切断工程の実績日報（添付配信）', 0, 1, 0, 0, 1),
('REPORT_INVENTORY_TREND_WEEKLY', '在庫推移レポート', '工程別在庫推移の週次レポート（添付配信）', 0, 1, 0, 0, 1),
('REPORT_PLAN_ACTUAL_MONTHLY', '計画実績対比レポート', '計画と実績の月次対比レポート（添付配信）', 0, 1, 0, 0, 1)
ON DUPLICATE KEY UPDATE event_name = VALUES(event_name), description = VALUES(description);

-- 報告定義シード
INSERT INTO report_definitions (report_code, report_name, category, default_format, parameter_schema, event_code, description, is_active)
VALUES
(
  'CUTTING_DAILY_ACTUAL', '切断工程実績レポート', 'MES', 'xlsx',
  '{"fields":[{"key":"date_range","label":"対象期間","type":"date_range","default":"yesterday","presets":["yesterday","today","last_week","this_week","last_month","this_month","custom"]}]}',
  'REPORT_CUTTING_DAILY_ACTUAL', '切断実績（設備別件数・数量・明細）を集計し添付配信', 1
),
(
  'INVENTORY_TREND_WEEKLY', '在庫推移レポート', 'ERP', 'xlsx',
  '{"fields":[{"key":"date_range","label":"対象期間","type":"date_range","default":"last_week","presets":["last_week","this_week","last_month","this_month","custom"]}]}',
  'REPORT_INVENTORY_TREND_WEEKLY', '工程別の在庫推移を集計し添付配信', 1
),
(
  'PLAN_ACTUAL_MONTHLY', '計画実績対比レポート', 'APS', 'xlsx',
  '{"fields":[{"key":"month","label":"基準月","type":"month","default":"last_month"}]}',
  'REPORT_PLAN_ACTUAL_MONTHLY', '計画（ベースライン）と実績の月次対比を集計し添付配信', 1
)
ON DUPLICATE KEY UPDATE report_name = VALUES(report_name), category = VALUES(category), default_format = VALUES(default_format), parameter_schema = VALUES(parameter_schema), event_code = VALUES(event_code), description = VALUES(description);

-- メールテンプレート（本文は要約 + 詳細は添付）
INSERT INTO email_templates (code, name, subject, body, event_code, language, variables, is_active)
VALUES
(
  'REPORT_CUTTING_DAILY_ACTUAL', '切断工程実績レポート',
  '【Smart-EMAP】{report_name} {period_label}（{record_count}件）',
  '<p>{report_name}をお届けします。</p><p>対象期間: {period_label}<br>件数: {record_count} 件<br>送信者: {sent_by}<br>送信日時: {sent_at}</p>{summary_html}<p>詳細は添付ファイルをご確認ください。</p><p>Smart-EMAP 生産管理システム</p>',
  'REPORT_CUTTING_DAILY_ACTUAL', 'ja',
  '["report_name","period_label","record_count","summary_html","sent_by","sent_at"]', 1
),
(
  'REPORT_INVENTORY_TREND_WEEKLY', '在庫推移レポート',
  '【Smart-EMAP】{report_name} {period_label}',
  '<p>{report_name}をお届けします。</p><p>対象期間: {period_label}<br>送信者: {sent_by}<br>送信日時: {sent_at}</p>{summary_html}<p>詳細は添付ファイルをご確認ください。</p><p>Smart-EMAP 生産管理システム</p>',
  'REPORT_INVENTORY_TREND_WEEKLY', 'ja',
  '["report_name","period_label","record_count","summary_html","sent_by","sent_at"]', 1
),
(
  'REPORT_PLAN_ACTUAL_MONTHLY', '計画実績対比レポート',
  '【Smart-EMAP】{report_name} {period_label}',
  '<p>{report_name}をお届けします。</p><p>基準月: {period_label}<br>送信者: {sent_by}<br>送信日時: {sent_at}</p>{summary_html}<p>詳細は添付ファイルをご確認ください。</p><p>Smart-EMAP 生産管理システム</p>',
  'REPORT_PLAN_ACTUAL_MONTHLY', 'ja',
  '["report_name","period_label","record_count","summary_html","sent_by","sent_at"]', 1
)
ON DUPLICATE KEY UPDATE name = VALUES(name), subject = VALUES(subject), body = VALUES(body), variables = VALUES(variables);

SET FOREIGN_KEY_CHECKS = 1;
