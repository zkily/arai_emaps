"""
標準原価・月次差異（cost_standard_versions / product_standard_costs ほか）
"""
from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CostStandardVersion(Base):
    __tablename__ = "cost_standard_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    fiscal_year = Column(Integer, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="draft")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    remarks = Column(Text)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product_costs = relationship("ProductStandardCost", back_populates="version", cascade="all, delete-orphan")


class ProductStandardCost(Base):
    __tablename__ = "product_standard_costs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("cost_standard_versions.id", ondelete="CASCADE"), nullable=False)
    product_cd = Column(String(50), nullable=False, index=True)
    product_name = Column(String(200))
    material_cost_std = Column(Numeric(18, 4), nullable=False, default=0)
    labor_cost_std = Column(Numeric(18, 4), nullable=False, default=0)
    overhead_cost_std = Column(Numeric(18, 4), nullable=False, default=0)
    total_cost_std = Column(Numeric(18, 4), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="JPY")
    source = Column(String(30), nullable=False, default="manual")
    remarks = Column(Text)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    version = relationship("CostStandardVersion", back_populates="product_costs")
    material_lines = relationship(
        "ProductStandardMaterialLine", back_populates="header", cascade="all, delete-orphan"
    )
    labor_lines = relationship(
        "ProductStandardLaborLine", back_populates="header", cascade="all, delete-orphan"
    )
    overhead_lines = relationship(
        "ProductStandardOverheadLine", back_populates="header", cascade="all, delete-orphan"
    )


class ProductStandardMaterialLine(Base):
    __tablename__ = "product_standard_material_lines"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    header_id = Column(BigInteger, ForeignKey("product_standard_costs.id", ondelete="CASCADE"), nullable=False)
    line_no = Column(Integer, nullable=False, default=1)
    material_cd = Column(String(50))
    material_name = Column(String(200))
    qty_per_unit = Column(Numeric(18, 6), nullable=False, default=0)
    scrap_pct = Column(Numeric(9, 4), nullable=False, default=0)
    standard_unit_price = Column(Numeric(18, 6), nullable=False, default=0)
    amount = Column(Numeric(18, 4), nullable=False, default=0)
    bom_line_id = Column(Integer)

    header = relationship("ProductStandardCost", back_populates="material_lines")


class ProductStandardLaborLine(Base):
    __tablename__ = "product_standard_labor_lines"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    header_id = Column(BigInteger, ForeignKey("product_standard_costs.id", ondelete="CASCADE"), nullable=False)
    line_no = Column(Integer, nullable=False, default=1)
    process_cd = Column(String(50))
    process_name = Column(String(200))
    std_hours = Column(Numeric(18, 6), nullable=False, default=0)
    setup_hours = Column(Numeric(18, 6), nullable=False, default=0)
    labor_rate_per_hour = Column(Numeric(18, 6), nullable=False, default=0)
    cost_center_cd = Column(String(50))
    amount = Column(Numeric(18, 4), nullable=False, default=0)

    header = relationship("ProductStandardCost", back_populates="labor_lines")


class ProductStandardOverheadLine(Base):
    __tablename__ = "product_standard_overhead_lines"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    header_id = Column(BigInteger, ForeignKey("product_standard_costs.id", ondelete="CASCADE"), nullable=False)
    line_no = Column(Integer, nullable=False, default=1)
    cost_center_cd = Column(String(50))
    allocation_basis = Column(String(40), nullable=False, default="machine_hours")
    basis_qty_per_unit = Column(Numeric(18, 6), nullable=False, default=0)
    overhead_rate = Column(Numeric(18, 6), nullable=False, default=0)
    amount = Column(Numeric(18, 4), nullable=False, default=0)

    header = relationship("ProductStandardCost", back_populates="overhead_lines")


class CostAccountingPeriod(Base):
    __tablename__ = "cost_accounting_periods"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year_month = Column(String(7), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="open")
    notes = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product_lines = relationship("CostPeriodProductCost", back_populates="period", cascade="all, delete-orphan")


class CostPeriodProductCost(Base):
    __tablename__ = "cost_period_product_costs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    period_id = Column(Integer, ForeignKey("cost_accounting_periods.id", ondelete="CASCADE"), nullable=False)
    version_id = Column(Integer, ForeignKey("cost_standard_versions.id", ondelete="SET NULL"))
    product_cd = Column(String(50), nullable=False, index=True)
    product_name = Column(String(200))
    finished_good_qty = Column(Numeric(18, 4), nullable=False, default=0)
    wip_equivalent_qty = Column(Numeric(18, 4), nullable=False, default=0)
    actual_material_cost = Column(Numeric(18, 2))
    actual_labor_cost = Column(Numeric(18, 2))
    actual_overhead_cost = Column(Numeric(18, 2))
    standard_material_allowed = Column(Numeric(18, 2), nullable=False, default=0)
    standard_labor_allowed = Column(Numeric(18, 2), nullable=False, default=0)
    standard_overhead_allowed = Column(Numeric(18, 2), nullable=False, default=0)
    variance_material_price = Column(Numeric(18, 2), nullable=False, default=0)
    variance_material_qty = Column(Numeric(18, 2), nullable=False, default=0)
    variance_labor_rate = Column(Numeric(18, 2), nullable=False, default=0)
    variance_labor_efficiency = Column(Numeric(18, 2), nullable=False, default=0)
    variance_moh_budget = Column(Numeric(18, 2), nullable=False, default=0)
    variance_moh_capacity = Column(Numeric(18, 2), nullable=False, default=0)
    variance_moh_efficiency = Column(Numeric(18, 2), nullable=False, default=0)
    remarks = Column(Text)
    updated_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    period = relationship("CostAccountingPeriod", back_populates="product_lines")
    version = relationship("CostStandardVersion")
