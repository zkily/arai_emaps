"""部品購買・在庫モデル（材料管理と同形のテーブル）"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric
from sqlalchemy.sql import func
from app.core.database import Base


class PartStock(Base):
    __tablename__ = "part_stock"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    part_cd = Column(String(50), nullable=False, index=True)
    part_name = Column(String(50), nullable=False)
    date = Column(Date, nullable=False, default="2025-01-01", index=True)
    initial_stock = Column(Integer, default=0)
    current_stock = Column(Integer, default=0, index=True)
    planned_usage = Column(Integer, default=0)
    usage_plan_qty = Column(Integer, nullable=False, default=0)
    stock_trend = Column(Integer, nullable=False, default=0)
    adjustment_quantity = Column(Integer, default=0)
    standard_spec = Column(String(50), default="")
    unit = Column(String(20))
    unit_price = Column(Numeric(15, 2), default=0.00)
    pieces_per_bundle = Column(Integer, default=0)
    supplier_cd = Column(String(15), index=True)
    supplier_name = Column(String(50))
    lead_time = Column(Integer, default=0)
    order_quantity = Column(Integer, default=0)
    order_bundle_quantity = Column(Integer, default=0)
    order_amount = Column(Numeric(15, 2), default=0.00)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
    remarks = Column(String(50), default="")
