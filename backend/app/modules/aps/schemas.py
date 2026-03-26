"""
APS Pydantic スキーマ（リクエスト / レスポンス）
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, time, datetime


# ──────────────────── Production Lines ────────────────────

class ProductionLineOut(BaseModel):
    id: int
    line_code: str
    line_name: str = Field(default="", description="設備名（machines.machine_name）")
    default_work_hours: float
    is_active: bool

    class Config:
        from_attributes = True


class EquipmentEfficiencyProductOut(BaseModel):
    """equipment_efficiency 1 行（APS 品名プルダウン用）"""
    id: int
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    efficiency_rate: float = 0.0
    step_time: Optional[int] = None
    lot_size: Optional[int] = Field(
        default=None,
        description="製品マスタ products.lot_size（product_cd 一致時）",
    )


# ──────────────────── Line Capacities ────────────────────

class LineCapacityItem(BaseModel):
    line_id: int
    work_date: date
    available_hours: float
    note: Optional[str] = None


class LineCapacityBatchBody(BaseModel):
    items: List[LineCapacityItem]


class LineCapacityOut(BaseModel):
    id: int
    line_id: int
    work_date: date
    available_hours: float
    note: Optional[str] = None

    class Config:
        from_attributes = True


# ──────────────────── Line Capacity Time Slots ────────────────────

class TimeSlotItem(BaseModel):
    start_time: time
    end_time: time
    sort_order: int = 0


class DaySlotsBody(BaseModel):
    line_id: int
    work_date: date
    slots: List[TimeSlotItem]


class TimeSlotOut(BaseModel):
    id: int
    start_time: time
    end_time: time
    sort_order: int

    class Config:
        from_attributes = True


class DaySlotsOut(BaseModel):
    work_date: date
    available_hours: float
    slots: List[TimeSlotOut]


class DaySlotsBatchBody(BaseModel):
    line_id: int
    days: List[DaySlotsBody]


# ──────────────────── Line Product Standard ────────────────────

class LineProductStandardBody(BaseModel):
    line_id: int
    product_cd: str
    std_qty_per_hour: float
    setup_time_min: int = 0
    efficiency_pct: float = 100.0


class LineProductStandardOut(BaseModel):
    id: int
    line_id: int
    product_cd: str
    std_qty_per_hour: float
    setup_time_min: int
    efficiency_pct: float

    class Config:
        from_attributes = True


# ──────────────────── Production Schedules ────────────────────

class ScheduleCreateBody(BaseModel):
    line_id: int
    order_no: Optional[int] = None
    order_id: Optional[int] = None
    item_name: str
    product_cd: Optional[str] = None
    material_shortage: bool = False
    lot_qty: int = 0
    planned_batch_count: Optional[int] = None
    lot_size_snapshot: Optional[int] = None
    planned_process_qty: Optional[int] = None
    prev_month_carryover: int = 0
    due_date: Optional[date] = None
    material_date: Optional[date] = None
    setup_time: int = 0
    efficiency: float = 100.0
    daily_capacity: int
    start_date: Optional[date] = None
    run_immediately: bool = True


class ScheduleUpdateBody(BaseModel):
    line_id: Optional[int] = None
    order_no: Optional[int] = None
    order_id: Optional[int] = None
    item_name: Optional[str] = None
    product_cd: Optional[str] = None
    material_shortage: Optional[bool] = None
    lot_qty: Optional[int] = None
    planned_batch_count: Optional[int] = None
    lot_size_snapshot: Optional[int] = None
    planned_process_qty: Optional[int] = None
    prev_month_carryover: Optional[int] = None
    due_date: Optional[date] = None
    material_date: Optional[date] = None
    setup_time: Optional[int] = None
    efficiency: Optional[float] = None
    daily_capacity: Optional[int] = None
    start_date: Optional[date] = None
    # 部分更新時は既定でエンジンを走らせない（ライン串接は replan-sequence で行う）
    run_immediately: bool = False


class ScheduleOut(BaseModel):
    id: int
    line_id: int
    order_no: Optional[int] = None
    order_id: Optional[int] = None
    item_name: str
    product_cd: Optional[str] = None
    material_shortage: bool
    lot_qty: int
    planned_batch_count: int = 0
    lot_size_snapshot: int = 0
    planned_process_qty: int
    prev_month_carryover: int
    due_date: Optional[date] = None
    material_date: Optional[date] = None
    setup_time: int
    efficiency: float
    daily_capacity: int
    planned_output_qty: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    completion_rate: Optional[float] = None
    status: str

    class Config:
        from_attributes = True


# ──────────────────── Scheduling Grid ────────────────────

class ScheduleGridRow(BaseModel):
    """一行 = 一個工単 + 展平された日別 planned_qty"""
    id: int
    order_no: Optional[int] = None
    item_name: str
    material_shortage: bool
    lot_qty: int
    planned_batch_count: int = 0
    lot_size_snapshot: int = 0
    planned_process_qty: int
    prev_month_carryover: int
    due_date: Optional[str] = None
    material_date: Optional[str] = None
    setup_time: int
    efficiency: float
    efficiency_rate: Optional[float] = None
    daily_capacity: int
    planned_output_qty: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    completion_rate: Optional[float] = None
    status: str
    daily: Dict[str, int] = Field(default_factory=dict)


class LineGridBlock(BaseModel):
    line_id: int
    line_code: str
    default_work_hours: float
    calendar: Dict[str, float] = Field(default_factory=dict)
    rows: List[ScheduleGridRow] = Field(default_factory=list)
    daily_totals: Dict[str, int] = Field(default_factory=dict)
    sum_planned_process_qty: int = 0
    sum_planned_output_qty: int = 0
    completion_rate: Optional[float] = None


class SchedulingGridResponse(BaseModel):
    dates: List[str]
    blocks: List[LineGridBlock]


# ──────────────────── Hourly slice grid（時間別ガント）────────────────────

class HourlyGridColumnOut(BaseModel):
    key: str
    work_date: str
    period_start: str
    period_end: str


class HourlyGridRowOut(BaseModel):
    schedule_id: int
    order_no: Optional[int] = None
    planned_batch_count: int = 0
    lot_size_snapshot: int = 0
    planned_process_qty: int = 0
    efficiency_rate: Optional[float] = None
    item_name: str
    slice_qty: Dict[str, int] = Field(default_factory=dict)


class SchedulingHourlyGridResponse(BaseModel):
    columns: List[HourlyGridColumnOut]
    rows: List[HourlyGridRowOut]


# ──────────────────── APS Batch Plans ────────────────────
class ApsBatchPlanOut(BaseModel):
    id: int
    aps_schedule_id: int
    production_month: date
    production_line: str
    priority_order: Optional[int] = None
    product_cd: str
    product_name: str
    planned_quantity: int
    production_lot_size: int
    lot_number: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str
