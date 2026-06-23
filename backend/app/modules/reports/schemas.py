"""レポート配信 Schemas"""
from __future__ import annotations

from datetime import datetime, time
from typing import Any, Optional

from pydantic import BaseModel, Field


class ReportDefinitionResponse(BaseModel):
    id: int
    report_code: str
    report_name: str
    category: str
    default_format: str
    parameter_schema: Optional[dict[str, Any]] = None
    event_code: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class ReportPreviewRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReportSendRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
    format: Optional[str] = None


class ReportDownloadRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
    format: Optional[str] = None


class ReportScheduleCreate(BaseModel):
    report_code: str
    schedule_type: str = "daily"
    schedule_time: time = time(8, 0)
    schedule_config: Optional[dict[str, Any]] = None
    parameters: Optional[dict[str, Any]] = None
    format: Optional[str] = None
    is_active: bool = True


class ReportScheduleUpdate(BaseModel):
    schedule_type: Optional[str] = None
    schedule_time: Optional[time] = None
    schedule_config: Optional[dict[str, Any]] = None
    parameters: Optional[dict[str, Any]] = None
    format: Optional[str] = None
    is_active: Optional[bool] = None


class ReportScheduleResponse(BaseModel):
    id: int
    report_code: str
    schedule_type: str
    schedule_time: time
    schedule_config: Optional[dict[str, Any]] = None
    parameters: Optional[dict[str, Any]] = None
    format: Optional[str] = None
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportSendLogResponse(BaseModel):
    id: int
    report_code: str
    trigger_type: str
    reference_key: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    recipient_count: int
    success_count: int
    status: str
    message: Optional[str] = None
    error_message: Optional[str] = None
    triggered_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
