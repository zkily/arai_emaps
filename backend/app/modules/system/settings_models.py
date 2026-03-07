"""
システム設定モデル
システムログ、採番ルール、ワークフロー、通知、データ管理
"""
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Date, Time, ForeignKey, Text, JSON, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


# ========== システムログ ==========

class OperationLog(Base):
    """操作ログテーブルモデル"""
    __tablename__ = "operation_logs"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="ID")
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), comment="日時")
    user_id = Column(Integer, nullable=True, comment="ユーザーID")
    username = Column(String(100), nullable=True, comment="ユーザー名")
    action = Column(String(50), nullable=False, comment="操作")
    module = Column(String(100), nullable=True, comment="モジュール名")
    target = Column(String(500), nullable=True, comment="対象")
    target_id = Column(Integer, nullable=True, comment="対象レコードID")
    ip_address = Column(String(45), nullable=True, comment="IPアドレス")
    user_agent = Column(Text, nullable=True, comment="ユーザーエージェント")
    details = Column(JSON, nullable=True, comment="詳細情報")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    
    def __repr__(self):
        return f"<OperationLog(id={self.id}, action='{self.action}', user='{self.username}')>"


class ErrorLog(Base):
    """エラーログテーブルモデル"""
    __tablename__ = "error_logs"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="ID")
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), comment="日時")
    level = Column(String(20), nullable=False, comment="レベル")
    source = Column(String(200), nullable=True, comment="ソース")
    message = Column(Text, nullable=False, comment="メッセージ")
    stack_trace = Column(Text, nullable=True, comment="スタックトレース")
    user_id = Column(Integer, nullable=True, comment="ユーザーID")
    request_id = Column(String(100), nullable=True, comment="リクエストID")
    extra_data = Column(JSON, nullable=True, comment="追加データ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, level='{self.level}', source='{self.source}')>"


class ApiLog(Base):
    """API連携ログテーブルモデル"""
    __tablename__ = "api_logs"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="ID")
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), comment="日時")
    method = Column(String(10), nullable=False, comment="HTTPメソッド")
    endpoint = Column(String(500), nullable=False, comment="エンドポイント")
    status_code = Column(Integer, nullable=False, comment="ステータスコード")
    duration = Column(Integer, nullable=True, comment="応答時間（ms）")
    client = Column(String(100), nullable=True, comment="クライアント")
    user_id = Column(Integer, nullable=True, comment="ユーザーID")
    ip_address = Column(String(45), nullable=True, comment="IPアドレス")
    request_body = Column(Text, nullable=True, comment="リクエストボディ")
    response_body = Column(Text, nullable=True, comment="レスポンスボディ")
    error_message = Column(Text, nullable=True, comment="エラーメッセージ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    
    def __repr__(self):
        return f"<ApiLog(id={self.id}, method='{self.method}', endpoint='{self.endpoint}')>"


# ========== 採番ルール ==========

class NumberingRule(Base):
    """採番ルールテーブルモデル"""
    __tablename__ = "numbering_rules"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="ルールコード")
    name = Column(String(100), nullable=False, comment="ルール名")
    prefix = Column(String(20), nullable=False, comment="プレフィックス")
    format = Column(String(100), nullable=False, comment="フォーマット")
    start_number = Column(Integer, nullable=False, default=1, comment="連番開始値")
    increment = Column(Integer, nullable=False, default=1, comment="連番増分")
    current_number = Column(Integer, nullable=False, default=0, comment="現在の連番")
    reset_type = Column(String(20), nullable=False, default="monthly", comment="リセットタイミング")
    last_reset_date = Column(Date, nullable=True, comment="最終リセット日")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    description = Column(Text, nullable=True, comment="説明")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    def __repr__(self):
        return f"<NumberingRule(id={self.id}, code='{self.code}', name='{self.name}')>"


# ========== ワークフロー ==========

class ApprovalRoute(Base):
    """承認ルートテーブルモデル"""
    __tablename__ = "approval_routes"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    name = Column(String(100), nullable=False, comment="ルート名")
    type = Column(String(20), nullable=False, comment="種類")
    condition_type = Column(String(50), nullable=True, comment="条件タイプ")
    condition_value = Column(String(200), nullable=True, comment="条件値")
    condition_min = Column(Numeric(15, 2), nullable=True, comment="金額条件（最小）")
    condition_max = Column(Numeric(15, 2), nullable=True, comment="金額条件（最大）")
    condition_department_id = Column(Integer, nullable=True, comment="部門条件")
    priority = Column(Integer, default=0, comment="優先度")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    # リレーション
    steps = relationship("ApprovalRouteStep", back_populates="route", cascade="all, delete-orphan", order_by="ApprovalRouteStep.step_order")
    
    def __repr__(self):
        return f"<ApprovalRoute(id={self.id}, name='{self.name}', type='{self.type}')>"


class ApprovalRouteStep(Base):
    """承認ルートステップテーブルモデル"""
    __tablename__ = "approval_route_steps"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    route_id = Column(Integer, ForeignKey("approval_routes.id", ondelete="CASCADE"), nullable=False, comment="承認ルートID")
    step_order = Column(Integer, nullable=False, comment="ステップ順序")
    step_name = Column(String(100), nullable=False, comment="ステップ名")
    approver_type = Column(String(20), nullable=False, comment="承認者タイプ")
    approver_id = Column(Integer, nullable=True, comment="承認者ID")
    approver_position = Column(String(50), nullable=True, comment="役職名")
    is_optional = Column(Boolean, default=False, comment="スキップ可能")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    
    # リレーション
    route = relationship("ApprovalRoute", back_populates="steps")
    
    def __repr__(self):
        return f"<ApprovalRouteStep(id={self.id}, route_id={self.route_id}, step='{self.step_name}')>"


class Delegation(Base):
    """代理承認テーブルモデル"""
    __tablename__ = "delegations"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    delegator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="委任者ID")
    delegate_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="代理者ID")
    start_date = Column(Date, nullable=False, comment="開始日")
    end_date = Column(Date, nullable=False, comment="終了日")
    scope = Column(String(50), nullable=False, default="all", comment="範囲")
    scope_details = Column(JSON, nullable=True, comment="範囲詳細")
    reason = Column(String(500), nullable=True, comment="理由")
    status = Column(String(20), nullable=False, default="active", comment="ステータス")
    created_by = Column(Integer, nullable=True, comment="作成者")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    def __repr__(self):
        return f"<Delegation(id={self.id}, delegator={self.delegator_id}, delegate={self.delegate_id})>"


class WorkflowDefinition(Base):
    """ワークフロー定義テーブルモデル"""
    __tablename__ = "workflow_definitions"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="コード")
    name = Column(String(100), nullable=False, comment="名前")
    document_type = Column(String(50), nullable=False, comment="対象伝票タイプ")
    approval_route_id = Column(Integer, ForeignKey("approval_routes.id", ondelete="SET NULL"), nullable=True, comment="承認ルートID")
    timeout_days = Column(Integer, default=3, comment="承認期限")
    escalation_enabled = Column(Boolean, default=False, comment="エスカレーション有効")
    escalation_days = Column(Integer, nullable=True, comment="エスカレーション日数")
    escalation_target = Column(String(100), nullable=True, comment="エスカレーション先")
    auto_approve_enabled = Column(Boolean, default=False, comment="自動承認有効")
    auto_approve_condition = Column(JSON, nullable=True, comment="自動承認条件")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    # リレーション
    approval_route = relationship("ApprovalRoute")
    
    def __repr__(self):
        return f"<WorkflowDefinition(id={self.id}, code='{self.code}', name='{self.name}')>"


# ========== 通知センター ==========

class NotificationSetting(Base):
    """通知設定テーブルモデル"""
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    event_code = Column(String(50), unique=True, nullable=False, index=True, comment="イベントコード")
    event_name = Column(String(100), nullable=False, comment="イベント名")
    description = Column(String(500), nullable=True, comment="説明")
    in_app_enabled = Column(Boolean, default=True, comment="アプリ内通知有効")
    email_enabled = Column(Boolean, default=False, comment="メール通知有効")
    slack_enabled = Column(Boolean, default=False, comment="Slack通知有効")
    line_enabled = Column(Boolean, default=False, comment="LINE通知有効")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    def __repr__(self):
        return f"<NotificationSetting(id={self.id}, event='{self.event_code}')>"


class EmailTemplate(Base):
    """メールテンプレートテーブルモデル"""
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="コード")
    name = Column(String(100), nullable=False, comment="名前")
    subject = Column(String(200), nullable=False, comment="件名")
    body = Column(Text, nullable=False, comment="本文")
    event_code = Column(String(50), nullable=True, comment="イベントコード")
    language = Column(String(10), default="ja", comment="言語")
    variables = Column(JSON, nullable=True, comment="利用可能変数")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, code='{self.code}', name='{self.name}')>"


class IntegrationConfig(Base):
    """外部連携設定テーブルモデル"""
    __tablename__ = "integration_configs"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    service_type = Column(String(50), unique=True, nullable=False, comment="サービスタイプ")
    config = Column(JSON, nullable=False, comment="設定情報")
    is_enabled = Column(Boolean, default=False, comment="有効フラグ")
    last_test_at = Column(DateTime, nullable=True, comment="最終テスト日時")
    last_test_result = Column(String(50), nullable=True, comment="最終テスト結果")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    def __repr__(self):
        return f"<IntegrationConfig(id={self.id}, service='{self.service_type}')>"


# ========== データ管理 ==========

class ImportExportHistory(Base):
    """インポート/エクスポート履歴テーブルモデル"""
    __tablename__ = "import_export_history"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    type = Column(String(20), nullable=False, comment="種類")
    master_type = Column(String(50), nullable=False, comment="マスター種類")
    filename = Column(String(255), nullable=False, comment="ファイル名")
    file_path = Column(String(500), nullable=True, comment="ファイルパス")
    format = Column(String(20), nullable=True, comment="フォーマット")
    encoding = Column(String(20), nullable=True, comment="文字コード")
    total_records = Column(Integer, default=0, comment="総件数")
    success_records = Column(Integer, default=0, comment="成功件数")
    error_records = Column(Integer, default=0, comment="エラー件数")
    status = Column(String(20), nullable=False, default="processing", comment="ステータス")
    error_details = Column(JSON, nullable=True, comment="エラー詳細")
    options = Column(JSON, nullable=True, comment="オプション")
    user_id = Column(Integer, nullable=True, comment="ユーザーID")
    started_at = Column(DateTime, nullable=True, comment="開始日時")
    completed_at = Column(DateTime, nullable=True, comment="完了日時")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    
    def __repr__(self):
        return f"<ImportExportHistory(id={self.id}, type='{self.type}', master='{self.master_type}')>"


class BackupSetting(Base):
    """バックアップ設定テーブルモデル"""
    __tablename__ = "backup_settings"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    auto_backup_enabled = Column(Boolean, default=False, comment="自動バックアップ有効")
    schedule = Column(String(20), nullable=False, default="daily", comment="スケジュール")
    schedule_time = Column(Time, default="02:00:00", comment="実行時刻")
    storage_path = Column(String(500), nullable=False, default="/backup/", comment="保存先")
    retention_count = Column(Integer, default=7, comment="保持世代数")
    include_files = Column(Boolean, default=False, comment="ファイル含む")
    compression_enabled = Column(Boolean, default=True, comment="圧縮有効")
    encryption_enabled = Column(Boolean, default=False, comment="暗号化有効")
    notify_on_complete = Column(Boolean, default=False, comment="完了時通知")
    notify_on_error = Column(Boolean, default=True, comment="エラー時通知")
    updated_by = Column(Integer, nullable=True, comment="更新者")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    def __repr__(self):
        return f"<BackupSetting(id={self.id}, auto={self.auto_backup_enabled})>"


class BackupHistory(Base):
    """バックアップ履歴テーブルモデル"""
    __tablename__ = "backup_history"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    filename = Column(String(255), nullable=False, comment="ファイル名")
    file_path = Column(String(500), nullable=False, comment="ファイルパス")
    file_size = Column(BigInteger, nullable=True, comment="ファイルサイズ")
    backup_type = Column(String(20), nullable=False, default="auto", comment="タイプ")
    status = Column(String(20), nullable=False, default="completed", comment="ステータス")
    error_message = Column(Text, nullable=True, comment="エラーメッセージ")
    started_at = Column(DateTime, nullable=True, comment="開始日時")
    completed_at = Column(DateTime, nullable=True, comment="完了日時")
    created_by = Column(Integer, nullable=True, comment="作成者")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    
    def __repr__(self):
        return f"<BackupHistory(id={self.id}, filename='{self.filename}')>"
