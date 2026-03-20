"""
APS 排産スケジューリング SQLAlchemy モデル
production_lines / line_capacities / production_schedules / schedule_details
"""
from sqlalchemy import (
    Column, Integer, String, Date, Numeric, Boolean, BigInteger,
    ForeignKey, DateTime, Text, TIMESTAMP,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProductionLine(Base):
    """生産ライン基礎情報"""
    __tablename__ = "production_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_code = Column(String(50), unique=True, nullable=False, index=True)
    default_work_hours = Column(Numeric(4, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    capacities = relationship("LineCapacity", back_populates="line", cascade="all, delete-orphan")
    schedules = relationship("ProductionSchedule", back_populates="line")


class LineCapacity(Base):
    """産線日別稼働カレンダー"""
    __tablename__ = "line_capacities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_id = Column(Integer, ForeignKey("production_lines.id", ondelete="CASCADE"), nullable=False)
    work_date = Column(Date, nullable=False)
    available_hours = Column(Numeric(4, 2), nullable=False)
    note = Column(String(255), nullable=True)

    line = relationship("ProductionLine", back_populates="capacities")


class ProductionSchedule(Base):
    """排産工単主計画表"""
    __tablename__ = "production_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_id = Column(Integer, ForeignKey("production_lines.id"), nullable=False)
    order_no = Column(Integer, nullable=True)
    order_id = Column(Integer, nullable=True)
    item_name = Column(String(100), nullable=False)
    material_shortage = Column(Boolean, nullable=False, default=False)
    lot_qty = Column(Integer, nullable=False, default=0)
    planned_process_qty = Column(Integer, nullable=False)
    prev_month_carryover = Column(Integer, nullable=False, default=0)
    due_date = Column(Date, nullable=True)
    material_date = Column(Date, nullable=True)
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

    line = relationship("ProductionLine", back_populates="schedules")
    details = relationship("ScheduleDetail", back_populates="schedule", cascade="all, delete-orphan")


class ScheduleDetail(Base):
    """毎日排産明細/甘特図データ"""
    __tablename__ = "schedule_details"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_id = Column(Integer, ForeignKey("production_schedules.id", ondelete="CASCADE"), nullable=False)
    schedule_date = Column(Date, nullable=False)
    planned_qty = Column(Integer, nullable=False, default=0)
    actual_qty = Column(Integer, nullable=False, default=0)

    schedule = relationship("ProductionSchedule", back_populates="details")
