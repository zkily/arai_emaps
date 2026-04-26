"""
倉庫日次在庫 shipping_warehouse_daily_stock
"""
from sqlalchemy import Column, BigInteger, String, Date, DateTime, Numeric
from sqlalchemy.sql import func

from app.core.database import Base


class ShippingWarehouseDailyStock(Base):
    """製品×納入先×日の倉庫日次在庫スナップショット"""

    __tablename__ = "shipping_warehouse_daily_stock"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_cd = Column(String(50), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    destination_cd = Column(String(50), nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
    weekday = Column(String(10), nullable=False)
    order_qty = Column(Numeric(18, 2), nullable=False, default=0)
    forecast_qty = Column(Numeric(18, 2), nullable=False, default=0)
    warehouse_carryover = Column(Numeric(18, 2), nullable=False, default=0)
    warehouse_actual = Column(Numeric(18, 2), nullable=False, default=0)
    warehouse_defect = Column(Numeric(18, 2), nullable=False, default=0)
    warehouse_disposal = Column(Numeric(18, 2), nullable=False, default=0)
    warehouse_hold = Column(Numeric(18, 2), nullable=False, default=0)
    warehouse_stock = Column(Numeric(18, 2), nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
