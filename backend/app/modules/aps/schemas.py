"""
APS Pydantic スキーマ（リクエスト / レスポンス）
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date


# ──────────────────── Production Lines ────────────────────

class ProductionLineOut(BaseModel):
    id: int
    line_code: str
    default_work_hours: float
    is_active: bool

    class Config:
        from_attributes = True


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


# ──────────────────── Production Schedules ────────────────────

class ScheduleCreateBody(BaseModel):
    line_id: int
    order_no: Optional[int] = None
    order_id: Optional[int] = None
    item_name: str
    material_shortage: bool = False
    lot_qty: int = 0
    planned_process_qty: int
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
    material_shortage: Optional[bool] = None
    lot_qty: Optional[int] = None
    planned_process_qty: Optional[int] = None
    prev_month_carryover: Optional[int] = None
    due_date: Optional[date] = None
    material_date: Optional[date] = None
    setup_time: Optional[int] = None
    efficiency: Optional[float] = None
    daily_capacity: Optional[int] = None
    start_date: Optional[date] = None
    run_immediately: bool = True


class ScheduleOut(BaseModel):
    id: int
    line_id: int
    order_no: Optional[int] = None
    order_id: Optional[int] = None
    item_name: str
    material_shortage: bool
    lot_qty: int
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
    planned_process_qty: int
    prev_month_carryover: int
    due_date: Optional[str] = None
    material_date: Optional[str] = None
    setup_time: int
    efficiency: float
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
