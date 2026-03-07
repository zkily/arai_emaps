"""
システム設定Schemas
システムログ、採番ルール、ワークフロー、通知、データ管理
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum


# ========== Enums ==========

class LogAction(str, Enum):
    login = "login"
    logout = "logout"
    create = "create"
    update = "update"
    delete = "delete"


class LogLevel(str, Enum):
    error = "ERROR"
    warn = "WARN"
    info = "INFO"


class ResetType(str, Enum):
    never = "never"
    daily = "daily"
    monthly = "monthly"
    yearly = "yearly"


class RouteType(str, Enum):
    amount = "amount"
    department = "department"
    custom = "custom"


class DelegationStatus(str, Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class ImportExportType(str, Enum):
    import_ = "import"
    export = "export"


class ImportExportStatus(str, Enum):
    processing = "processing"
    success = "success"
    partial_error = "partial_error"
    failed = "failed"


class BackupType(str, Enum):
    auto = "auto"
    manual = "manual"


class BackupStatus(str, Enum):
    completed = "completed"
    failed = "failed"


# ========== システムログ Schemas ==========

class OperationLogBase(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    module: Optional[str] = None
    target: Optional[str] = None
    target_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None


class OperationLogCreate(OperationLogBase):
    pass


class OperationLogResponse(OperationLogBase):
    id: int
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class OperationLogSearchParams(BaseModel):
    user: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedOperationLogs(BaseModel):
    items: List[OperationLogResponse]
    total: int
    page: int
    page_size: int


class ErrorLogBase(BaseModel):
    level: str
    source: Optional[str] = None
    message: str
    stack_trace: Optional[str] = None
    user_id: Optional[int] = None
    request_id: Optional[str] = None
    extra_data: Optional[dict] = None


class ErrorLogCreate(ErrorLogBase):
    pass


class ErrorLogResponse(ErrorLogBase):
    id: int
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class ErrorLogSearchParams(BaseModel):
    level: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedErrorLogs(BaseModel):
    items: List[ErrorLogResponse]
    total: int
    page: int
    page_size: int


class ApiLogBase(BaseModel):
    method: str
    endpoint: str
    status_code: int
    duration: Optional[int] = None
    client: Optional[str] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None


class ApiLogCreate(ApiLogBase):
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None


class ApiLogResponse(ApiLogBase):
    id: int
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApiLogSearchParams(BaseModel):
    endpoint: Optional[str] = None
    status: Optional[str] = None  # success, client_error, server_error
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedApiLogs(BaseModel):
    items: List[ApiLogResponse]
    total: int
    page: int
    page_size: int


class LogStats(BaseModel):
    """今日のログ統計"""
    operation_count: int = 0
    error_count: int = 0
    api_count: int = 0


# ========== 採番ルール Schemas ==========

class NumberingRuleBase(BaseModel):
    code: str = Field(..., max_length=50, description="ルールコード")
    name: str = Field(..., max_length=100, description="ルール名")
    prefix: str = Field(..., max_length=20, description="プレフィックス")
    format: str = Field(..., max_length=100, description="フォーマット")
    start_number: int = Field(1, ge=1, description="連番開始値")
    increment: int = Field(1, ge=1, description="連番増分")
    reset_type: str = Field("monthly", description="リセットタイミング")
    description: Optional[str] = None


class NumberingRuleCreate(NumberingRuleBase):
    pass


class NumberingRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    prefix: Optional[str] = Field(None, max_length=20)
    format: Optional[str] = Field(None, max_length=100)
    start_number: Optional[int] = Field(None, ge=1)
    increment: Optional[int] = Field(None, ge=1)
    reset_type: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class NumberingRuleResponse(NumberingRuleBase):
    id: int
    current_number: int
    last_reset_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    example: Optional[str] = None  # 計算されたサンプル番号
    
    class Config:
        from_attributes = True


class NumberingRuleListResponse(BaseModel):
    id: int
    code: str
    name: str
    prefix: str
    format: str
    example: str
    current_number: int
    reset_type: str
    is_active: bool
    
    class Config:
        from_attributes = True


class GeneratedNumber(BaseModel):
    """生成された番号"""
    number: str
    rule_code: str


# ========== ワークフロー Schemas ==========

class ApprovalRouteStepBase(BaseModel):
    step_order: int = Field(..., ge=1, description="ステップ順序")
    step_name: str = Field(..., max_length=100, description="ステップ名")
    approver_type: str = Field(..., description="承認者タイプ")
    approver_id: Optional[int] = None
    approver_position: Optional[str] = None
    is_optional: bool = False


class ApprovalRouteStepCreate(ApprovalRouteStepBase):
    pass


class ApprovalRouteStepResponse(ApprovalRouteStepBase):
    id: int
    route_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApprovalRouteBase(BaseModel):
    name: str = Field(..., max_length=100, description="ルート名")
    type: str = Field(..., description="種類")
    condition_type: Optional[str] = None
    condition_value: Optional[str] = None
    condition_min: Optional[Decimal] = None
    condition_max: Optional[Decimal] = None
    condition_department_id: Optional[int] = None
    priority: int = Field(0, description="優先度")


class ApprovalRouteCreate(ApprovalRouteBase):
    steps: List[ApprovalRouteStepCreate] = []


class ApprovalRouteUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = None
    condition_type: Optional[str] = None
    condition_value: Optional[str] = None
    condition_min: Optional[Decimal] = None
    condition_max: Optional[Decimal] = None
    condition_department_id: Optional[int] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    steps: Optional[List[ApprovalRouteStepCreate]] = None


class ApprovalRouteResponse(ApprovalRouteBase):
    id: int
    is_active: bool
    steps: List[ApprovalRouteStepResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApprovalRouteListResponse(BaseModel):
    id: int
    name: str
    type: str
    condition: str  # 表示用条件文字列
    steps: List[str]  # ステップ名の配列
    is_active: bool
    
    class Config:
        from_attributes = True


class DelegationBase(BaseModel):
    delegator_id: int = Field(..., description="委任者ID")
    delegate_id: int = Field(..., description="代理者ID")
    start_date: date
    end_date: date
    scope: str = Field("all", description="範囲")
    scope_details: Optional[dict] = None
    reason: Optional[str] = Field(None, max_length=500)


class DelegationCreate(DelegationBase):
    pass


class DelegationUpdate(BaseModel):
    delegate_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    scope: Optional[str] = None
    scope_details: Optional[dict] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class DelegationResponse(DelegationBase):
    id: int
    status: str
    delegator_name: Optional[str] = None  # JOIN結果
    delegate_name: Optional[str] = None   # JOIN結果
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowDefinitionBase(BaseModel):
    code: str = Field(..., max_length=50, description="コード")
    name: str = Field(..., max_length=100, description="名前")
    document_type: str = Field(..., max_length=50, description="対象伝票")
    approval_route_id: Optional[int] = None
    timeout_days: int = Field(3, ge=1, description="承認期限")
    escalation_enabled: bool = False
    escalation_days: Optional[int] = None
    escalation_target: Optional[str] = None
    auto_approve_enabled: bool = False
    auto_approve_condition: Optional[dict] = None


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    pass


class WorkflowDefinitionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    document_type: Optional[str] = None
    approval_route_id: Optional[int] = None
    timeout_days: Optional[int] = None
    escalation_enabled: Optional[bool] = None
    escalation_days: Optional[int] = None
    escalation_target: Optional[str] = None
    auto_approve_enabled: Optional[bool] = None
    auto_approve_condition: Optional[dict] = None
    is_active: Optional[bool] = None


class WorkflowDefinitionResponse(WorkflowDefinitionBase):
    id: int
    is_active: bool
    approval_route_name: Optional[str] = None  # JOIN結果
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ========== 通知センター Schemas ==========

class NotificationSettingBase(BaseModel):
    event_code: str = Field(..., max_length=50)
    event_name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    in_app_enabled: bool = True
    email_enabled: bool = False
    slack_enabled: bool = False
    line_enabled: bool = False


class NotificationSettingCreate(NotificationSettingBase):
    pass


class NotificationSettingUpdate(BaseModel):
    event_name: Optional[str] = None
    description: Optional[str] = None
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    slack_enabled: Optional[bool] = None
    line_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class NotificationSettingResponse(NotificationSettingBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmailTemplateBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=200)
    body: str
    event_code: Optional[str] = None
    language: str = Field("ja", max_length=10)
    variables: Optional[List[str]] = None


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    event_code: Optional[str] = None
    language: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(EmailTemplateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IntegrationConfigBase(BaseModel):
    service_type: str = Field(..., max_length=50)
    config: dict
    is_enabled: bool = False


class IntegrationConfigCreate(IntegrationConfigBase):
    pass


class IntegrationConfigUpdate(BaseModel):
    config: Optional[dict] = None
    is_enabled: Optional[bool] = None


class IntegrationConfigResponse(IntegrationConfigBase):
    id: int
    last_test_at: Optional[datetime] = None
    last_test_result: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IntegrationTestResult(BaseModel):
    success: bool
    message: str


# ========== データ管理 Schemas ==========

class ImportExportHistoryBase(BaseModel):
    type: str
    master_type: str
    filename: str


class ImportExportHistoryResponse(ImportExportHistoryBase):
    id: int
    file_path: Optional[str] = None
    format: Optional[str] = None
    encoding: Optional[str] = None
    total_records: int
    success_records: int
    error_records: int
    status: str
    error_details: Optional[dict] = None
    options: Optional[dict] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None  # JOIN結果
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ImportRequest(BaseModel):
    master_type: str = Field(..., description="マスター種類")
    update_existing: bool = Field(False, description="既存データを更新")
    skip_errors: bool = Field(True, description="エラー行をスキップ")


class ExportRequest(BaseModel):
    master_type: str = Field(..., description="マスター種類")
    format: str = Field("csv", description="フォーマット")
    encoding: str = Field("utf8", description="文字コード")


class BackupSettingBase(BaseModel):
    auto_backup_enabled: bool = False
    schedule: str = Field("daily", description="スケジュール")
    schedule_time: Optional[time] = None
    storage_path: str = Field("/backup/", max_length=500)
    retention_count: int = Field(7, ge=1, le=30)
    include_files: bool = False
    compression_enabled: bool = True
    encryption_enabled: bool = False
    notify_on_complete: bool = False
    notify_on_error: bool = True


class BackupSettingUpdate(BackupSettingBase):
    pass


class BackupSettingResponse(BackupSettingBase):
    id: int
    updated_by: Optional[int] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BackupHistoryResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: Optional[int] = None
    file_size_display: Optional[str] = None  # "125MB"形式
    backup_type: str
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ManualBackupRequest(BaseModel):
    include_files: bool = False


class RestoreRequest(BaseModel):
    backup_id: int


class DataResetRequest(BaseModel):
    targets: List[str] = Field(..., description="初期化対象")
    confirmation: str = Field(..., description="確認文字列")
