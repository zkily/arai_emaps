"""
外注管理 データベースモデル（outsourcing_suppliers / welding_orders / welding_receivings）
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Date, Numeric, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class OutsourcingSupplier(Base):
    """外注先マスタテーブル（outsourcing_suppliers）"""
    __tablename__ = "outsourcing_suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_cd = Column(String(10), unique=True, nullable=False, index=True)
    supplier_name = Column(String(50), nullable=False)
    supplier_type = Column(String(20), nullable=False, default="plating", index=True)  # plating, welding, cutting, forming, parts_processing
    postal_code = Column(String(10))
    address = Column(String(50))
    phone = Column(String(20))
    fax = Column(String(20))
    contact_person = Column(String(50))
    email = Column(String(50))
    payment_terms = Column(String(50))
    lead_time_days = Column(Integer, default=7)
    remarks = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class WeldingOrder(Base):
    """外注溶接注文（outsourcing_welding_orders）"""
    __tablename__ = "outsourcing_welding_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_no = Column(String(30), unique=True, nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    supplier_cd = Column(String(20), nullable=False, index=True)
    product_cd = Column(String(50), nullable=False, index=True)
    product_name = Column(String(200))
    specification = Column(String(200))
    welding_type = Column(String(50), nullable=False)
    welding_points = Column(Integer, default=0)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(10), default="個")
    unit_price = Column(Numeric(12, 2), default=0)
    delivery_date = Column(Date)
    delivery_location = Column(String(100))
    category = Column(String(50))
    content = Column(Text)
    received_qty = Column(Integer, default=0)
    status = Column(String(20), default="pending", index=True)  # pending, ordered, partial, completed, cancelled
    remarks = Column(Text)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class OutsourcingProcessProduct(Base):
    """外注工程製品マスタ（outsourcing_process_products）"""
    __tablename__ = "outsourcing_process_products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    process_type = Column(String(30), nullable=False, index=True)  # cutting, forming, plating, welding, inspection, processing
    supplier_cd = Column(String(20), nullable=False, index=True)
    supplier_name = Column(String(100))
    product_cd = Column(String(50), nullable=False, index=True)
    product_name = Column(String(200))
    specification = Column(String(200))
    unit_price = Column(Numeric(12, 2), default=0)
    delivery_lead_time = Column(Integer, default=7)
    delivery_location = Column(String(100))
    category = Column(String(50))
    content = Column(Text)
    remarks = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(50))
    updated_by = Column(String(50))


class WeldingReceiving(Base):
    """外注溶接受入（outsourcing_welding_receivings）"""
    __tablename__ = "outsourcing_welding_receivings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    receiving_no = Column(String(30), unique=True, nullable=False, index=True)
    receiving_date = Column(Date, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("outsourcing_welding_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    order_no = Column(String(30), nullable=False, index=True)
    supplier_cd = Column(String(20), nullable=False, index=True)
    product_cd = Column(String(50), nullable=False)
    product_name = Column(String(200))
    welding_type = Column(String(50))
    welding_points = Column(Integer, default=0)
    delivery_location = Column(String(100))
    category = Column(String(50))
    content = Column(Text)
    specification = Column(String(200))
    order_qty = Column(Integer, nullable=False)
    receiving_qty = Column(Integer, nullable=False)
    good_qty = Column(Integer, default=0)
    defect_qty = Column(Integer, default=0)
    defect_reason = Column(String(100))
    status = Column(String(20), default="pending", index=True)  # pending, inspected, defect
    inspector = Column(String(50))
    remarks = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
