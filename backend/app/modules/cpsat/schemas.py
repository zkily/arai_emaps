"""CP-SAT 作業展開のリクエスト / レスポンス"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

QtySource = Literal["confirmed", "forecast", "confirmed_or_forecast"]


class ExpandRunIn(BaseModel):
    due_from: date = Field(..., description="交期開始（含む）")
    due_to: date = Field(..., description="交期終了（含む）")
    product_cds: Optional[list[str]] = Field(None, description="製品CD絞り込み。未指定は全製品")
    qty_source: QtySource = "confirmed"
    name: Optional[str] = Field(None, max_length=100)
    max_jobs: Optional[int] = Field(None, ge=1, le=20000, description="展開する最大ジョブ数")


class SolveRunIn(BaseModel):
    max_solve_seconds: Optional[int] = Field(
        None, ge=1, le=3600, description="ソルバ上限秒（未指定は実行時設定）"
    )
    objective_type: Optional[Literal["tardiness", "makespan", "weighted"]] = None


class ExpandWarningOut(BaseModel):
    skipped_no_qty: int = 0
    skipped_no_due: int = 0
    skipped_no_route: int = 0
    skipped_no_ops: int = 0
    incomplete_no_machine: int = 0
    incomplete_zero_ptime: int = 0
    skipped_product_cds: list[str] = Field(default_factory=list)


class CandidateOut(BaseModel):
    id: int
    machine_cd: str
    machine_name: Optional[str] = None
    process_time_sec: float
    setup_time_sec: int
    processing_sec: int
    is_assigned: bool = False


class OperationOut(BaseModel):
    id: int
    op_index: int
    step_no: int
    process_cd: str
    process_name: Optional[str] = None
    yield_percent: float
    wait_sec_after: int
    q_input: int
    q_output: int
    start_sec: Optional[int] = None
    end_sec: Optional[int] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    assigned_machine_cd: Optional[str] = None
    assigned_machine_name: Optional[str] = None
    processing_sec: Optional[int] = None
    setup_sec: Optional[int] = None
    candidate_count: int = 0
    candidates: Optional[list[CandidateOut]] = None


class JobOut(BaseModel):
    id: int
    job_index: int
    source_type: str
    source_id: Optional[int] = None
    order_no: Optional[str] = None
    product_cd: str
    product_name: Optional[str] = None
    q_target: int
    q_start: int
    lot_size: Optional[int] = None
    lot_index: Optional[int] = None
    lot_count: Optional[int] = None
    due_at: Optional[datetime] = None
    due_sec: Optional[int] = None
    last_op_end_sec: Optional[int] = None
    tardiness_sec: Optional[int] = None
    operation_count: int = 0
    incomplete: bool = False
    operations: Optional[list[OperationOut]] = None


class RunOut(BaseModel):
    id: int
    run_code: Optional[str] = None
    name: Optional[str] = None
    horizon_start: datetime
    horizon_end: datetime
    time_unit_sec: int
    objective_type: str
    status: str
    solver_status: Optional[str] = None
    wall_time_sec: Optional[float] = None
    makespan_sec: Optional[int] = None
    total_tardiness_sec: Optional[int] = None
    objective_value: Optional[float] = None
    job_count: int
    operation_count: int
    error_message: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    warnings: Optional[ExpandWarningOut] = None
    jobs: Optional[list[JobOut]] = None
