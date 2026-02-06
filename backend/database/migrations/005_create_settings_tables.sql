-- ============================================================
-- システム設定テーブル作成 (MySQL)
-- システムログ、採番ルール、ワークフロー、通知、データ管理
-- ============================================================

-- ========== システムログ関連 ==========

-- 操作ログテーブル
CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
    user_id INT NULL COMMENT 'ユーザーID',
    username VARCHAR(100) NULL COMMENT 'ユーザー名',
    action VARCHAR(50) NOT NULL COMMENT '操作（login/logout/create/update/delete）',
    module VARCHAR(100) NULL COMMENT 'モジュール名',
    target VARCHAR(500) NULL COMMENT '対象（例: 受注番号: SO-202602-0156）',
    target_id INT NULL COMMENT '対象レコードID',
    ip_address VARCHAR(45) NULL COMMENT 'IPアドレス',
    user_agent TEXT NULL COMMENT 'ユーザーエージェント',
    details JSON NULL COMMENT '詳細情報（変更前後の値など）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_operation_logs_timestamp (timestamp),
    INDEX idx_operation_logs_user (user_id),
    INDEX idx_operation_logs_action (action),
    INDEX idx_operation_logs_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作ログテーブル';


-- エラーログテーブル
CREATE TABLE IF NOT EXISTS error_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
    level VARCHAR(20) NOT NULL COMMENT 'レベル（ERROR/WARN/INFO）',
    source VARCHAR(200) NULL COMMENT 'ソース（サービス名・ファイル名）',
    message TEXT NOT NULL COMMENT 'エラーメッセージ',
    stack_trace TEXT NULL COMMENT 'スタックトレース',
    user_id INT NULL COMMENT 'ユーザーID',
    request_id VARCHAR(100) NULL COMMENT 'リクエストID',
    extra_data JSON NULL COMMENT '追加データ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_error_logs_timestamp (timestamp),
    INDEX idx_error_logs_level (level),
    INDEX idx_error_logs_source (source(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='エラーログテーブル';


-- API連携ログテーブル
CREATE TABLE IF NOT EXISTS api_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日時',
    method VARCHAR(10) NOT NULL COMMENT 'HTTPメソッド（GET/POST/PUT/DELETE）',
    endpoint VARCHAR(500) NOT NULL COMMENT 'エンドポイント',
    status_code INT NOT NULL COMMENT 'HTTPステータスコード',
    duration INT NULL COMMENT '応答時間（ミリ秒）',
    client VARCHAR(100) NULL COMMENT 'クライアント（Web Frontend/Mobile App等）',
    user_id INT NULL COMMENT 'ユーザーID',
    ip_address VARCHAR(45) NULL COMMENT 'IPアドレス',
    request_body TEXT NULL COMMENT 'リクエストボディ',
    response_body TEXT NULL COMMENT 'レスポンスボディ（エラー時のみ）',
    error_message TEXT NULL COMMENT 'エラーメッセージ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_api_logs_timestamp (timestamp),
    INDEX idx_api_logs_endpoint (endpoint(200)),
    INDEX idx_api_logs_status (status_code),
    INDEX idx_api_logs_method (method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API連携ログテーブル';


-- ========== 採番ルール ==========

CREATE TABLE IF NOT EXISTS numbering_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'ルールコード（例: SALES_ORDER）',
    name VARCHAR(100) NOT NULL COMMENT 'ルール名（例: 受注番号）',
    prefix VARCHAR(20) NOT NULL COMMENT 'プレフィックス（例: SO）',
    format VARCHAR(100) NOT NULL COMMENT 'フォーマット（例: {PREFIX}-{YYYY}{MM}-{SEQ:4}）',
    start_number INT NOT NULL DEFAULT 1 COMMENT '連番開始値',
    increment INT NOT NULL DEFAULT 1 COMMENT '連番増分',
    current_number INT NOT NULL DEFAULT 0 COMMENT '現在の連番',
    reset_type VARCHAR(20) NOT NULL DEFAULT 'monthly' COMMENT 'リセットタイミング（never/daily/monthly/yearly）',
    last_reset_date DATE NULL COMMENT '最終リセット日',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    description TEXT NULL COMMENT '説明',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_numbering_rules_code (code),
    INDEX idx_numbering_rules_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='採番ルールテーブル';


-- ========== ワークフロー関連 ==========

-- 承認ルートテーブル
CREATE TABLE IF NOT EXISTS approval_routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT 'ルート名',
    type VARCHAR(20) NOT NULL COMMENT '種類（amount:金額, department:部門, custom:カスタム）',
    condition_type VARCHAR(50) NULL COMMENT '条件タイプ',
    condition_value VARCHAR(200) NULL COMMENT '条件値（例: 10万円未満, 営業部）',
    condition_min DECIMAL(15,2) NULL COMMENT '金額条件（最小）',
    condition_max DECIMAL(15,2) NULL COMMENT '金額条件（最大）',
    condition_department_id INT NULL COMMENT '部門条件',
    priority INT DEFAULT 0 COMMENT '優先度（同条件時の判定順序）',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_approval_routes_type (type),
    INDEX idx_approval_routes_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='承認ルートテーブル';


-- 承認ルートステップテーブル
CREATE TABLE IF NOT EXISTS approval_route_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL COMMENT '承認ルートID',
    step_order INT NOT NULL COMMENT 'ステップ順序（1から開始）',
    step_name VARCHAR(100) NOT NULL COMMENT 'ステップ名（例: 課長）',
    approver_type VARCHAR(20) NOT NULL COMMENT '承認者タイプ（role:ロール, user:特定ユーザー, position:役職）',
    approver_id INT NULL COMMENT '承認者ID（ユーザーID or ロールID）',
    approver_position VARCHAR(50) NULL COMMENT '役職名',
    is_optional TINYINT(1) DEFAULT 0 COMMENT 'スキップ可能フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_route_steps_route (route_id),
    INDEX idx_route_steps_order (route_id, step_order),
    CONSTRAINT fk_route_steps_route FOREIGN KEY (route_id) REFERENCES approval_routes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='承認ルートステップテーブル';


-- 代理承認テーブル
CREATE TABLE IF NOT EXISTS delegations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    delegator_id INT NOT NULL COMMENT '委任者ユーザーID',
    delegate_id INT NOT NULL COMMENT '代理者ユーザーID',
    start_date DATE NOT NULL COMMENT '開始日',
    end_date DATE NOT NULL COMMENT '終了日',
    scope VARCHAR(50) NOT NULL DEFAULT 'all' COMMENT '範囲（all:全承認, specific:特定）',
    scope_details JSON NULL COMMENT '範囲詳細（特定の場合）',
    reason VARCHAR(500) NULL COMMENT '理由',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'ステータス（active/expired/cancelled）',
    created_by INT NULL COMMENT '作成者',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_delegations_delegator (delegator_id),
    INDEX idx_delegations_delegate (delegate_id),
    INDEX idx_delegations_dates (start_date, end_date),
    INDEX idx_delegations_status (status),
    CONSTRAINT fk_delegations_delegator FOREIGN KEY (delegator_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_delegations_delegate FOREIGN KEY (delegate_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代理承認テーブル';


-- ワークフロー定義テーブル
CREATE TABLE IF NOT EXISTS workflow_definitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'ワークフローコード（例: WF_PO）',
    name VARCHAR(100) NOT NULL COMMENT 'ワークフロー名',
    document_type VARCHAR(50) NOT NULL COMMENT '対象伝票タイプ',
    approval_route_id INT NULL COMMENT 'デフォルト承認ルートID',
    timeout_days INT DEFAULT 3 COMMENT '承認期限（日数）',
    escalation_enabled TINYINT(1) DEFAULT 0 COMMENT 'エスカレーション有効',
    escalation_days INT NULL COMMENT 'エスカレーションまでの日数',
    escalation_target VARCHAR(100) NULL COMMENT 'エスカレーション先',
    auto_approve_enabled TINYINT(1) DEFAULT 0 COMMENT '自動承認有効',
    auto_approve_condition JSON NULL COMMENT '自動承認条件',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_workflow_defs_code (code),
    INDEX idx_workflow_defs_doctype (document_type),
    CONSTRAINT fk_workflow_defs_route FOREIGN KEY (approval_route_id) REFERENCES approval_routes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ワークフロー定義テーブル';


-- ========== 通知センター ==========

-- 通知設定テーブル
CREATE TABLE IF NOT EXISTS notification_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_code VARCHAR(50) NOT NULL UNIQUE COMMENT 'イベントコード',
    event_name VARCHAR(100) NOT NULL COMMENT 'イベント名',
    description VARCHAR(500) NULL COMMENT '説明',
    in_app_enabled TINYINT(1) DEFAULT 1 COMMENT 'アプリ内通知有効',
    email_enabled TINYINT(1) DEFAULT 0 COMMENT 'メール通知有効',
    slack_enabled TINYINT(1) DEFAULT 0 COMMENT 'Slack通知有効',
    line_enabled TINYINT(1) DEFAULT 0 COMMENT 'LINE通知有効',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_notification_settings_event (event_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知設定テーブル';


-- メールテンプレートテーブル
CREATE TABLE IF NOT EXISTS email_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE COMMENT 'テンプレートコード',
    name VARCHAR(100) NOT NULL COMMENT 'テンプレート名',
    subject VARCHAR(200) NOT NULL COMMENT '件名（変数可）',
    body TEXT NOT NULL COMMENT '本文（HTML可、変数可）',
    event_code VARCHAR(50) NULL COMMENT '関連イベントコード',
    language VARCHAR(10) DEFAULT 'ja' COMMENT '言語',
    variables JSON NULL COMMENT '利用可能な変数一覧',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '有効フラグ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    INDEX idx_email_templates_code (code),
    INDEX idx_email_templates_event (event_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='メールテンプレートテーブル';


-- 外部連携設定テーブル
CREATE TABLE IF NOT EXISTS integration_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_type VARCHAR(50) NOT NULL UNIQUE COMMENT 'サービスタイプ（slack/line/teams等）',
    config JSON NOT NULL COMMENT '設定情報（webhook_url, token等）',
    is_enabled TINYINT(1) DEFAULT 0 COMMENT '有効フラグ',
    last_test_at DATETIME NULL COMMENT '最終テスト日時',
    last_test_result VARCHAR(50) NULL COMMENT '最終テスト結果',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外部連携設定テーブル';


-- ========== データ管理 ==========

-- インポート/エクスポート履歴テーブル
CREATE TABLE IF NOT EXISTS import_export_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(20) NOT NULL COMMENT '種類（import/export）',
    master_type VARCHAR(50) NOT NULL COMMENT 'マスター種類',
    filename VARCHAR(255) NOT NULL COMMENT 'ファイル名',
    file_path VARCHAR(500) NULL COMMENT 'ファイルパス',
    format VARCHAR(20) NULL COMMENT 'フォーマット（csv/xlsx）',
    encoding VARCHAR(20) NULL COMMENT '文字コード',
    total_records INT DEFAULT 0 COMMENT '総件数',
    success_records INT DEFAULT 0 COMMENT '成功件数',
    error_records INT DEFAULT 0 COMMENT 'エラー件数',
    status VARCHAR(20) NOT NULL DEFAULT 'processing' COMMENT 'ステータス（processing/success/partial_error/failed）',
    error_details JSON NULL COMMENT 'エラー詳細',
    options JSON NULL COMMENT 'オプション（update_existing等）',
    user_id INT NULL COMMENT '実行ユーザーID',
    started_at DATETIME NULL COMMENT '開始日時',
    completed_at DATETIME NULL COMMENT '完了日時',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_import_export_type (type),
    INDEX idx_import_export_master (master_type),
    INDEX idx_import_export_status (status),
    INDEX idx_import_export_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='インポート/エクスポート履歴テーブル';


-- バックアップ設定テーブル
CREATE TABLE IF NOT EXISTS backup_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    auto_backup_enabled TINYINT(1) DEFAULT 0 COMMENT '自動バックアップ有効',
    schedule VARCHAR(20) NOT NULL DEFAULT 'daily' COMMENT 'スケジュール（daily/weekly/monthly）',
    schedule_time TIME DEFAULT '02:00:00' COMMENT '実行時刻',
    storage_path VARCHAR(500) NOT NULL DEFAULT '/backup/' COMMENT '保存先パス',
    retention_count INT DEFAULT 7 COMMENT '保持世代数',
    include_files TINYINT(1) DEFAULT 0 COMMENT 'ファイルも含める',
    compression_enabled TINYINT(1) DEFAULT 1 COMMENT '圧縮有効',
    encryption_enabled TINYINT(1) DEFAULT 0 COMMENT '暗号化有効',
    notify_on_complete TINYINT(1) DEFAULT 0 COMMENT '完了時通知',
    notify_on_error TINYINT(1) DEFAULT 1 COMMENT 'エラー時通知',
    updated_by INT NULL COMMENT '更新者',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='バックアップ設定テーブル';


-- バックアップ履歴テーブル
CREATE TABLE IF NOT EXISTS backup_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL COMMENT 'ファイル名',
    file_path VARCHAR(500) NOT NULL COMMENT 'ファイルパス',
    file_size BIGINT NULL COMMENT 'ファイルサイズ（バイト）',
    backup_type VARCHAR(20) NOT NULL DEFAULT 'auto' COMMENT 'タイプ（auto/manual）',
    status VARCHAR(20) NOT NULL DEFAULT 'completed' COMMENT 'ステータス（completed/failed）',
    error_message TEXT NULL COMMENT 'エラーメッセージ',
    started_at DATETIME NULL COMMENT '開始日時',
    completed_at DATETIME NULL COMMENT '完了日時',
    created_by INT NULL COMMENT '作成者（手動の場合）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    INDEX idx_backup_history_type (backup_type),
    INDEX idx_backup_history_status (status),
    INDEX idx_backup_history_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='バックアップ履歴テーブル';


-- ========== 初期データ投入 ==========

-- デフォルト採番ルール
INSERT INTO numbering_rules (code, name, prefix, format, start_number, increment, current_number, reset_type) VALUES
('SALES_ORDER', '受注番号', 'SO', '{PREFIX}-{YYYY}{MM}-{SEQ:4}', 1, 1, 0, 'monthly'),
('QUOTATION', '見積番号', 'QT', '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', 1, 1, 0, 'daily'),
('PURCHASE_ORDER', '発注番号', 'PO', '{PREFIX}-{YYYY}-{SEQ:5}', 1, 1, 0, 'yearly'),
('INVOICE', '請求書番号', 'INV', '{PREFIX}{YYYY}{MM}-{SEQ:4}', 1, 1, 0, 'monthly'),
('SHIPMENT', '出荷番号', 'SHP', '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', 1, 1, 0, 'daily')
ON DUPLICATE KEY UPDATE name = VALUES(name);


-- デフォルト承認ルート
INSERT INTO approval_routes (name, type, condition_value, condition_min, condition_max, priority) VALUES
('通常購買承認', 'amount', '10万円未満', NULL, 100000, 1),
('高額購買承認', 'amount', '10万円以上100万円未満', 100000, 1000000, 2),
('大規模購買承認', 'amount', '100万円以上', 1000000, NULL, 3)
ON DUPLICATE KEY UPDATE name = VALUES(name);


-- 承認ルートステップ（通常購買承認）
INSERT INTO approval_route_steps (route_id, step_order, step_name, approver_type, approver_position)
SELECT id, 1, '申請者', 'position', '申請者' FROM approval_routes WHERE name = '通常購買承認' LIMIT 1
ON DUPLICATE KEY UPDATE step_name = VALUES(step_name);
INSERT INTO approval_route_steps (route_id, step_order, step_name, approver_type, approver_position)
SELECT id, 2, '課長', 'position', '課長' FROM approval_routes WHERE name = '通常購買承認' LIMIT 1
ON DUPLICATE KEY UPDATE step_name = VALUES(step_name);
INSERT INTO approval_route_steps (route_id, step_order, step_name, approver_type, approver_position)
SELECT id, 3, '部長', 'position', '部長' FROM approval_routes WHERE name = '通常購買承認' LIMIT 1
ON DUPLICATE KEY UPDATE step_name = VALUES(step_name);


-- デフォルト通知設定
INSERT INTO notification_settings (event_code, event_name, description, in_app_enabled, email_enabled, slack_enabled, line_enabled) VALUES
('APPROVAL_REQUEST', '承認依頼', '新しい承認依頼が届いた時', 1, 1, 1, 0),
('APPROVAL_COMPLETE', '承認完了', '承認が完了した時', 1, 1, 0, 0),
('APPROVAL_REJECT', '承認却下', '承認が却下された時', 1, 1, 1, 0),
('DELIVERY_ALERT', '納期アラート', '納期が近づいている時', 1, 1, 1, 1),
('STOCK_ALERT', '在庫アラート', '在庫が基準値を下回った時', 1, 1, 1, 0),
('SYSTEM_ERROR', 'システムエラー', 'システムエラーが発生した時', 1, 1, 1, 0)
ON DUPLICATE KEY UPDATE event_name = VALUES(event_name);


-- デフォルトメールテンプレート
INSERT INTO email_templates (code, name, subject, body, event_code, language) VALUES
('APPROVAL_REQUEST', '承認依頼', '【要承認】{document_type} #{document_no}', '<p>{approver_name}様</p><p>以下の承認依頼が届いています。</p><p>伝票種類: {document_type}<br>伝票番号: {document_no}<br>申請者: {requester_name}<br>金額: {amount}</p><p>システムにログインして承認処理を行ってください。</p>', 'APPROVAL_REQUEST', 'ja'),
('APPROVAL_COMPLETE', '承認完了', '【承認完了】{document_type} #{document_no}', '<p>{requester_name}様</p><p>以下の申請が承認されました。</p><p>伝票種類: {document_type}<br>伝票番号: {document_no}<br>承認者: {approver_name}</p>', 'APPROVAL_COMPLETE', 'ja'),
('PASSWORD_RESET', 'パスワードリセット', '【Smart-EMAP】パスワードリセット', '<p>{user_name}様</p><p>パスワードがリセットされました。</p><p>新しいパスワードでログインしてください。</p>', NULL, 'ja'),
('WELCOME', 'ようこそ', '【Smart-EMAP】アカウント作成完了', '<p>{user_name}様</p><p>Smart-EMAPへようこそ！</p><p>アカウントが作成されました。以下の情報でログインしてください。</p><p>ユーザー名: {username}<br>初期パスワード: {initial_password}</p>', NULL, 'ja')
ON DUPLICATE KEY UPDATE name = VALUES(name);


-- デフォルトバックアップ設定
INSERT INTO backup_settings (id, auto_backup_enabled, schedule, schedule_time, storage_path, retention_count) VALUES
(1, 1, 'daily', '02:00:00', '/backup/', 7)
ON DUPLICATE KEY UPDATE auto_backup_enabled = VALUES(auto_backup_enabled);


-- デフォルトワークフロー定義
INSERT INTO workflow_definitions (code, name, document_type, timeout_days, escalation_enabled)
SELECT 'WF_PO', '購買発注承認', '発注書', 3, 1
WHERE NOT EXISTS (SELECT 1 FROM workflow_definitions WHERE code = 'WF_PO');

INSERT INTO workflow_definitions (code, name, document_type, timeout_days, escalation_enabled)
SELECT 'WF_SO', '受注承認', '受注書', 2, 1
WHERE NOT EXISTS (SELECT 1 FROM workflow_definitions WHERE code = 'WF_SO');

INSERT INTO workflow_definitions (code, name, document_type, timeout_days, escalation_enabled)
SELECT 'WF_QT', '見積承認', '見積書', 1, 0
WHERE NOT EXISTS (SELECT 1 FROM workflow_definitions WHERE code = 'WF_QT');

INSERT INTO workflow_definitions (code, name, document_type, timeout_days, escalation_enabled)
SELECT 'WF_INV', '請求書承認', '請求書', 5, 1
WHERE NOT EXISTS (SELECT 1 FROM workflow_definitions WHERE code = 'WF_INV');
