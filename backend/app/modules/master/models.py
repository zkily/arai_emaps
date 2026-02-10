"""
製品マスタ データベースモデル（products テーブル）
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, Text, Numeric, Float  # Date used by DestinationHoliday; Time by Carrier
from sqlalchemy.sql import func
from app.core.database import Base


class Product(Base):
    """製品マスタテーブル（products）"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_cd = Column(String(50), unique=True, nullable=False, index=True)
    product_name = Column(String(100), nullable=False)
    product_type = Column(String(50))
    location_cd = Column(String(50), default="製品倉庫")
    start_use_date = Column(Date)
    category = Column(String(50))
    department_id = Column(Integer)
    destination_cd = Column(String(50))
    process_count = Column(Integer, default=1)
    lead_time = Column(Integer)
    lot_size = Column(Integer, default=1)
    is_multistage = Column(Boolean, default=True)
    priority = Column(Integer, default=2)
    status = Column(String(20), default="active")
    part_number = Column(String(50))
    vehicle_model = Column(String(50))
    box_type = Column(String(50))
    unit_per_box = Column(Integer)
    dimensions = Column(String(100))
    weight = Column(Numeric(10, 2))
    material_cd = Column(String(50))
    cut_length = Column(Numeric(10, 2))
    chamfer_length = Column(Numeric(10, 2))
    developed_length = Column(Numeric(10, 2))
    take_count = Column(Integer)
    scrap_length = Column(Numeric(10, 2))
    bom_id = Column(Integer)
    route_cd = Column(String(20))
    note = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    safety_days = Column(Integer)
    unit_price = Column(Numeric(10, 2))
    product_alias = Column(String(100))


class Material(Base):
    """材料マスタテーブル（materials）"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_cd = Column(String(50), unique=True, nullable=False, index=True)
    material_name = Column(String(100), nullable=False)
    material_type = Column(String(50))
    standard_spec = Column(String(100))
    unit = Column(String(20))
    diameter = Column(Numeric(10, 2))
    thickness = Column(Numeric(10, 2))
    length = Column(Numeric(10, 2))
    supply_classification = Column(String(50))
    pieces_per_bundle = Column(Integer)
    usegae = Column(String(100))
    supplier_cd = Column(String(50))
    unit_price = Column(Numeric(10, 2))
    long_weight = Column(Numeric(10, 2))
    single_price = Column(Numeric(10, 2))
    safety_stock = Column(Integer, default=0)
    lead_time = Column(Integer)
    storage_location = Column(String(100))
    status = Column(Integer, default=1)
    tolerance_range = Column(String(50))
    tolerance_1 = Column(Numeric(10, 3))
    tolerance_2 = Column(Numeric(10, 3))
    range_value = Column(String(50))
    min_value = Column(Numeric(10, 2))
    max_value = Column(Numeric(10, 2))
    actual_value_1 = Column(Numeric(10, 3))
    actual_value_2 = Column(Numeric(10, 3))
    actual_value_3 = Column(Numeric(10, 3))
    representative_model = Column(String(100))
    note = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Supplier(Base):
    """仕入先マスタテーブル（suppliers）"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_cd = Column(String(50), unique=True, nullable=False, index=True)
    supplier_name = Column(String(100), nullable=False)
    supplier_kana = Column(String(100))
    contact_person = Column(String(100))
    phone = Column(String(20))
    fax = Column(String(20))
    email = Column(String(100))
    postal_code = Column(String(10))
    address1 = Column(String(200))
    address2 = Column(String(200))
    payment_terms = Column(String(50))
    currency = Column(String(10), default="JPY")
    remarks = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Process(Base):
    """工程マスタ（processes）"""
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    process_cd = Column(String(20), unique=True, nullable=False, index=True)
    process_name = Column(String(60), nullable=False)
    short_name = Column(String(20))
    category = Column(String(20), index=True)
    is_outsource = Column(Integer, default=0)  # 0=社内, 1=外注
    default_cycle_sec = Column(Float, default=0.0)
    default_yield = Column(Numeric(5, 3), default=1.000)
    capacity_unit = Column(String(10), default="pcs")  # pcs, kg, m
    remark = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProcessRoute(Base):
    """工程ルートヘッダ（process_routes）"""
    __tablename__ = "process_routes"
    __table_args__ = ({"mysql_comment": "工程ルート（ヘッダ）"})

    id = Column(Integer, autoincrement=True, primary_key=True)
    route_cd = Column(String(20), unique=True, nullable=False, index=True)
    route_name = Column(String(100), nullable=False)
    description = Column(String(255))
    is_active = Column(Integer, default=1)  # 使用フラグ
    is_default = Column(Integer, default=0)  # デフォルトフラグ
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProcessRouteStep(Base):
    """工程ルートステップ（process_route_steps）"""
    __tablename__ = "process_route_steps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    route_cd = Column(String(15), nullable=False, index=True)
    step_no = Column(Integer, nullable=False)
    process_cd = Column(String(20), nullable=False)
    yield_percent = Column(Numeric(5, 2), default=100.00)
    cycle_sec = Column(Numeric(5, 2), default=0.00)
    remarks = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Destination(Base):
    """納入先マスタ（destinations）"""
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    destination_cd = Column(String(50), unique=True, nullable=False, index=True)
    destination_name = Column(String(100), nullable=False)
    customer_cd = Column(String(50))
    carrier_cd = Column(String(50))
    delivery_lead_time = Column(Integer, default=0)
    issue_type = Column(String(2), default="自動")
    phone = Column(String(20))
    address = Column(String(255))
    status = Column(Integer, default=1)  # 1=有効, 0=無効
    picked_id = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DestinationHoliday(Base):
    """納入先休日（destination_holidays）"""
    __tablename__ = "destination_holidays"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    destination_cd = Column(String(50), nullable=False, index=True)
    holiday_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now())


class DestinationWorkday(Base):
    """納入先臨時出勤日（destination_workdays）"""
    __tablename__ = "destination_workdays"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    destination_cd = Column(String(50), nullable=False, index=True)
    work_date = Column(Date, nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime, default=func.now())


class Customer(Base):
    """顧客マスタ（customers）"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_cd = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    address = Column(String(255))
    customer_type = Column(String(50))
    status = Column(Integer, default=1)  # 1=有効, 0=無効
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Carrier(Base):
    """運送便マスタ（carriers）"""
    __tablename__ = "carriers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    carrier_cd = Column(String(50), unique=True, nullable=False, index=True)
    carrier_name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    shipping_time = Column(Time)
    report_no = Column(String(50))
    note = Column(Text)
    status = Column(Integer, default=1)  # 1=有効, 0=無効
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Machine(Base):
    """設備マスタ（machines）"""
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_cd = Column(String(50), unique=True, nullable=False, index=True)
    machine_name = Column(String(100), nullable=False)
    machine_type = Column(String(50))
    status = Column(String(20), default="active")  # active / inactive / maintenance
    available_from = Column(Time, default=None)
    available_to = Column(Time, default=None)
    calendar_id = Column(Integer)
    efficiency = Column(Numeric(5, 2), default=100.00)
    note = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProductRouteStep(Base):
    """製品別工程ルートステップ（product_route_steps）"""
    __tablename__ = "product_route_steps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_cd = Column(String(50), nullable=False, index=True)
    route_cd = Column(String(50), nullable=False, index=True)
    step_no = Column(Integer, nullable=False)
    process_cd = Column(String(50), nullable=False)
    machine_id = Column(String(50))
    standard_cycle_time = Column(Numeric(10, 2))
    setup_time = Column(Numeric(10, 2))
    remarks = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProductRouteStepMachine(Base):
    """製品別工程ステップ設備（product_route_step_machines）"""
    __tablename__ = "product_route_step_machines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_cd = Column(String(50), nullable=False, index=True)
    route_cd = Column(String(50), nullable=False, index=True)
    step_no = Column(Integer, nullable=False)
    machine_cd = Column(String(50), nullable=False, index=True)
    machine_name = Column(String(100))
    process_time_sec = Column(Numeric(4, 2), default=0)
    setup_time = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
