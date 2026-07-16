"""予算管理 Pydantic スキーマ"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BudgetMonthKey(BaseModel):
    year: int
    month: int


class BudgetMonthlyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    month: int
    development_code: Optional[str] = None
    part_number: str
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    budget_qty: int = 0
    match_status: str = "unmatched"
    import_batch_id: Optional[int] = None
    source_file_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BudgetImportBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    months_json: Optional[str] = None
    total_rows: int = 0
    matched_rows: int = 0
    unmatched_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    uploaded_by: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None


class BudgetWorkingDaysItem(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=12)
    working_days: int = Field(..., ge=0, le=31)
    remark: Optional[str] = None


class BudgetWorkingDaysBatchUpdate(BaseModel):
    items: list[BudgetWorkingDaysItem] = Field(default_factory=list)


class BudgetWorkingDaysOut(BaseModel):
    year: int
    month: int
    label: str
    working_days: int = 0
    total_budget_qty: int = 0
    avg_daily_qty: Optional[int] = None


class BudgetProcessWorkingDaysItem(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=12)
    process_cd: str
    process_name: Optional[str] = None
    # None = 上書き削除（共通デフォルトに戻す）
    working_days: Optional[int] = Field(None, ge=0, le=31)
    remark: Optional[str] = None


class BudgetProcessWorkingDaysBatchUpdate(BaseModel):
    items: list[BudgetProcessWorkingDaysItem] = Field(default_factory=list)


class BudgetUploadResult(BaseModel):
    success: bool = True
    batch_id: int
    file_name: str
    months: list[BudgetMonthKey] = Field(default_factory=list)
    total_rows: int = 0
    matched_rows: int = 0
    unmatched_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    unmatched_samples: list[dict[str, Any]] = Field(default_factory=list)
    message: str = ""


class BudgetSummaryOut(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    product_count: int = 0
    matched_count: int = 0
    unmatched_count: int = 0
    total_budget_qty: int = 0
    month_count: int = 0


class ProcessLoadItem(BaseModel):
    process_cd: str
    process_name: str
    product_count: int = 0
    total_budget_qty: int = 0
    total_hours: float = 0.0
    is_outsource: int = 0


class EquipmentLoadItem(BaseModel):
    machine_cd: str
    machine_name: str
    product_count: int = 0
    total_budget_qty: int = 0
    total_hours: float = 0.0
    avg_efficiency_rate: Optional[float] = None


class CostAnalysisItem(BaseModel):
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    part_number: str
    development_code: Optional[str] = None
    budget_qty: int = 0
    unit_price: Optional[float] = None
    unit_cost_std: Optional[float] = None
    sales_amount: float = 0.0
    cost_amount: float = 0.0
    margin_amount: float = 0.0
