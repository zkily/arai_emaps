"""部品購買・在庫モデル（材料管理と同形のテーブル）"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Date, Numeric, Time
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


class PartLog(Base):
    """部品受入ログ（part_logs）"""
    __tablename__ = "part_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item = Column(String(100), nullable=False, comment="項目")
    part_cd = Column(String(50), nullable=False, index=True, comment="部品CD")
    part_name = Column(String(255), comment="部品名")
    process_cd = Column(String(50), nullable=False, index=True, comment="工程CD")
    log_date = Column(Date, nullable=False, index=True, comment="日付")
    log_time = Column(Time, nullable=False, comment="時間")
    hd_no = Column(String(50), comment="HD番号")
    pieces_per_bundle = Column(Integer, comment="1束あたりの本数")
    quantity = Column(Integer, comment="数量")
    bundle_quantity = Column(Integer, comment="束数量")
    manufacture_no = Column(String(255), index=True, comment="製造番号")
    manufacture_date = Column(Date, comment="製造日")
    length = Column(Integer, comment="長さ(mm)")
    outer_diameter1 = Column(Numeric(10, 4), comment="外径1(mm)")
    outer_diameter2 = Column(Numeric(10, 4), comment="外径2(mm)")
    magnetic = Column(String(1), comment="磁気")
    appearance = Column(String(1), comment="外観")
    supplier = Column(String(255), index=True, comment="仕入先")
    part_quality = Column(String(100), comment="部品規格")
    remarks = Column(Text, comment="備考")
    note = Column(String(255), comment="メモ")
    created_at = Column(DateTime, default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新日時")
