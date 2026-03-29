from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, Field


class CuttingPlannerAutoScheduleBody(BaseModel):
    production_month: str = Field(..., description="生産月 YYYY-MM")
    machine_ids: Optional[List[int]] = Field(default=None, description="対象切断機ID")
    start_date: Optional[date] = Field(default=None, description="排産開始日")
    horizon_days: int = Field(default=45, ge=7, le=120, description="排産対象日数")
    preserve_published: bool = Field(default=True, description="既に下発済みの計画を固定で保持")


class CuttingPlannerSyncFromInstructionsBody(BaseModel):
    production_month: str = Field(..., description="生産月 YYYY-MM")


class CuttingPlannerScheduleSelectedBody(BaseModel):
    production_month: str = Field(..., description="生産月 YYYY-MM")
    run_id: int = Field(..., description="cutting_plan_runs.id")
    item_ids: List[int] = Field(..., min_length=1, description="排産する cutting_plan_items.id")
    machine_ids: Optional[List[int]] = Field(default=None, description="対象切断機ID（未指定は全切断機）")
    start_date: Optional[date] = Field(default=None, description="排産開始日")
    horizon_days: int = Field(default=45, ge=7, le=120, description="排産対象日数")


class CuttingPlannerReorderBody(BaseModel):
    run_id: int
    machine_id: int
    ordered_item_ids: List[int] = Field(default_factory=list)
    horizon_days: int = Field(default=45, ge=7, le=120)


class CuttingPlannerPublishBody(BaseModel):
    run_id: int
    item_ids: Optional[List[int]] = Field(default=None, description="指定時は対象アイテムのみ")
    overwrite_existing: bool = Field(default=False, description="同一管理コード既存行がある場合に上書き")


class CuttingPlannerLockBody(BaseModel):
    run_id: int
    item_id: int
    is_locked: bool


class CuttingPlannerMachineOut(BaseModel):
    id: int
    machine_cd: str
    machine_name: str
    default_work_hours: Optional[float] = None


class CuttingPlannerListItemOut(BaseModel):
    id: int
    instruction_plan_id: Optional[int] = None
    product_cd: str
    product_name: str
    material_name: Optional[str] = None
    production_line: Optional[str] = None
    planned_quantity: int
    instruction_production_quantity: int = 0
    production_lot_size: Optional[int] = None
    lot_number: Optional[str] = None
    take_count: Optional[int] = None
    cutting_length: Optional[float] = None
    assigned_machine_id: Optional[int] = None
    assigned_machine: Optional[str] = None
    sequence_no: int
    planned_day: Optional[date] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    estimated_minutes: float
    efficiency_rate: Optional[float] = None
    setup_time_min: Optional[int] = None
    is_locked: bool
    publish_status: str
    published_cutting_id: Optional[int] = None
    actual_quantity: int = 0
    completion_status: str
    source_management_code: Optional[str] = None


class CuttingPlannerDayCellOut(BaseModel):
    item_id: int
    sequence_no: int
    product_name: str
    product_cd: str
    planned_quantity: int
    daily: dict[str, int]


class CuttingPlannerBlockOut(BaseModel):
    machine_id: int
    machine_name: str
    rows: List[CuttingPlannerDayCellOut]
    daily_totals: dict[str, int]


class CuttingPlannerGanttOut(BaseModel):
    dates: List[str]
    blocks: List[CuttingPlannerBlockOut]


class CuttingPlannerHourlyColumnOut(BaseModel):
    key: str
    work_date: str
    period_start: str
    period_end: str


class CuttingPlannerHourlyRowOut(BaseModel):
    item_id: int
    sequence_no: int
    product_name: str
    product_cd: str
    planned_quantity: int
    slice_qty: dict[str, int]


class CuttingPlannerHourlyGanttOut(BaseModel):
    columns: List[CuttingPlannerHourlyColumnOut]
    rows: List[CuttingPlannerHourlyRowOut]


class CuttingPlannerProgressOut(BaseModel):
    production_month: str
    run_id: Optional[int] = None
    total_items: int
    planned_items: int
    published_items: int
    in_progress_items: int
    completed_items: int
    total_planned_quantity: int
    total_instruction_production_quantity: int = 0
    total_actual_quantity: int


class CuttingPlannerReportItemOut(BaseModel):
    machine_name: Optional[str] = None
    planned_day: Optional[str] = None
    sequence_no: int
    product_cd: str
    product_name: str
    material_name: Optional[str] = None
    planned_quantity: int
    instruction_production_quantity: int = 0
    estimated_minutes: float
    publish_status: str
    completion_status: str


class CuttingPlannerReportOut(BaseModel):
    production_month: str
    generated_at: Optional[str] = None
    items: List[CuttingPlannerReportItemOut]


class CuttingPlannerTimeSlice(BaseModel):
    work_date: date
    period_start: time
    period_end: time
    planned_qty: int
