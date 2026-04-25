"""
APS 排産スケジューリング SQLAlchemy モデル
設備は machines マスタ（line_id は machines.id を参照）
line_capacities / production_schedules / schedule_details
"""
from sqlalchemy import (
    Column, Integer, String, Date, Time, Numeric, Boolean, BigInteger,
    SmallInteger, ForeignKey, TIMESTAMP, DateTime,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class LineCapacity(Base):
    """産線日別稼働カレンダー（line_id = machines.id）"""
    __tablename__ = "line_capacities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    work_date = Column(Date, nullable=False)
    available_hours = Column(Numeric(4, 2), nullable=False)
    note = Column(String(255), nullable=True)

    machine = relationship("Machine", foreign_keys=[line_id])


class LineCapacityTimeSlot(Base):
    """設備日別稼働時間帯"""
    __tablename__ = "line_capacity_time_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    work_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    sort_order = Column(SmallInteger, nullable=False, default=0)
    is_rest = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    machine = relationship("Machine", foreign_keys=[line_id])


class LineProductStandard(Base):
    """産線×製品 標準工時マスタ"""
    __tablename__ = "line_product_standard"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    product_cd = Column(String(50), nullable=False)
    std_qty_per_hour = Column(Numeric(10, 2), nullable=False, default=0.00)
    setup_time_min = Column(Integer, nullable=False, default=0)
    efficiency_pct = Column(Numeric(5, 2), nullable=False, default=100.00)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    machine = relationship("Machine", foreign_keys=[line_id])


class ProductionSchedule(Base):
    """排産工単主計画表"""
    __tablename__ = "production_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    order_no = Column(Integer, nullable=True)
    order_id = Column(Integer, nullable=True)
    item_name = Column(String(100), nullable=False)
    product_cd = Column(String(50), nullable=True)
    material_shortage = Column(Boolean, nullable=False, default=False)
    lot_qty = Column(Integer, nullable=False, default=0)
    planned_batch_count = Column(Integer, nullable=False, default=0)
    lot_size_snapshot = Column(Integer, nullable=False, default=0)
    planned_process_qty = Column(Integer, nullable=False)
    prev_month_carryover = Column(Integer, nullable=False, default=0)
    due_date = Column(Date, nullable=True)
    material_date = Column(Date, nullable=True)
    forced_start_date = Column(Date, nullable=True)
    setup_time = Column(Integer, nullable=False, default=0)
    efficiency = Column(Numeric(5, 2), nullable=False, default=100.00)
    daily_capacity = Column(Integer, nullable=False)
    planned_output_qty = Column(Integer, nullable=False, default=0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    completion_rate = Column(Numeric(5, 2), nullable=True)
    status = Column(String(20), nullable=False, default="PLANNING")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    machine = relationship("Machine", foreign_keys=[line_id])
    details = relationship("ScheduleDetail", back_populates="schedule", cascade="all, delete-orphan")
    slice_allocations = relationship(
        "ScheduleSliceAllocation",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )


class ScheduleSliceAllocation(Base):
    """排産時間帯別配分（ガント時間別）"""
    __tablename__ = "schedule_slice_allocations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey("production_schedules.id", ondelete="CASCADE"), nullable=False)
    work_date = Column(Date, nullable=False)
    period_start = Column(Time, nullable=False)
    period_end = Column(Time, nullable=False)
    planned_qty = Column(Integer, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    schedule = relationship("ProductionSchedule", back_populates="slice_allocations")


class ScheduleDetail(Base):
    """毎日排産明細/甘特図データ"""
    __tablename__ = "schedule_details"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey("production_schedules.id", ondelete="CASCADE"), nullable=False)
    schedule_date = Column(Date, nullable=False)
    planned_qty = Column(Integer, nullable=False, default=0)
    actual_qty = Column(Integer, nullable=False, default=0)
    defect_qty = Column(
        Integer,
        nullable=False,
        default=0,
        comment="日次不良数（在庫ログ transaction_type=不良 かつ process_cd=KT04 の quantity 合算）",
    )
    remaining_qty = Column(Integer, nullable=False, default=0)

    schedule = relationship("ProductionSchedule", back_populates="details")


class ApsLineReplanAnchor(Base):
    """設備別・順次再計算の開始アンカー日（replan-sequence で API 引数より優先）"""
    __tablename__ = "aps_line_replan_anchors"

    line_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"), primary_key=True)
    anchor_date = Column(Date, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    machine = relationship("Machine", foreign_keys=[line_id])


class ApsBatchPlan(Base):
    """APS ロット（lot_number）計画表（instruction_plans へ同期可能）"""
    __tablename__ = "aps_batch_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aps_schedule_id = Column(Integer, nullable=False, index=True)
    production_month = Column(Date, nullable=False)
    production_line = Column(String(50), nullable=False)
    priority_order = Column(Integer, nullable=True)
    product_cd = Column(String(50), nullable=False)
    product_name = Column(String(255), nullable=False)
    planned_quantity = Column(Integer, nullable=False, default=0)
    upstream_defect_qty = Column(
        Integer,
        nullable=False,
        default=0,
        comment="前工程不良合計（切断+面取、management_code 照合）",
    )
    original_planned_quantity = Column(Integer, nullable=True)
    production_lot_size = Column(Integer, nullable=False, default=0)
    lot_number = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="PLANNED")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
