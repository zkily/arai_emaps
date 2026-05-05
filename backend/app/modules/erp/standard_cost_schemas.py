"""
標準原価 API 用 Pydantic スキーマ
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


def _num(v) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


class CostStandardVersionBase(BaseModel):
    code: str
    fiscal_year: int
    status: str = "draft"
    effective_from: date
    effective_to: Optional[date] = None
    remarks: Optional[str] = None


class CostStandardVersionCreate(CostStandardVersionBase):
    pass


class CostStandardVersionUpdate(BaseModel):
    code: Optional[str] = None
    fiscal_year: Optional[int] = None
    status: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    remarks: Optional[str] = None


class CostStandardVersionOut(CostStandardVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- 明細 ---

class ProductStandardMaterialLineIn(BaseModel):
    line_no: int = 1
    material_cd: Optional[str] = None
    material_name: Optional[str] = None
    qty_per_unit: Decimal = Field(default=Decimal("0"))
    scrap_pct: Decimal = Field(default=Decimal("0"))
    standard_unit_price: Decimal = Field(default=Decimal("0"))
    amount: Decimal = Field(default=Decimal("0"))
    bom_line_id: Optional[int] = None


class ProductStandardLaborLineIn(BaseModel):
    line_no: int = 1
    process_cd: Optional[str] = None
    process_name: Optional[str] = None
    std_hours: Decimal = Field(default=Decimal("0"))
    setup_hours: Decimal = Field(default=Decimal("0"))
    labor_rate_per_hour: Decimal = Field(default=Decimal("0"))
    cost_center_cd: Optional[str] = None
    amount: Decimal = Field(default=Decimal("0"))


class ProductStandardOverheadLineIn(BaseModel):
    line_no: int = 1
    cost_center_cd: Optional[str] = None
    allocation_basis: str = "machine_hours"
    basis_qty_per_unit: Decimal = Field(default=Decimal("0"))
    overhead_rate: Decimal = Field(default=Decimal("0"))
    amount: Decimal = Field(default=Decimal("0"))


class ProductStandardMaterialLineOut(ProductStandardMaterialLineIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    header_id: int


class ProductStandardLaborLineOut(ProductStandardLaborLineIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    header_id: int


class ProductStandardOverheadLineOut(ProductStandardOverheadLineIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    header_id: int


class ProductStandardCostListItem(BaseModel):
    """一覧用（明細なし）"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_id: int
    product_cd: str
    product_name: Optional[str] = None
    material_cost_std: float = 0
    labor_cost_std: float = 0
    overhead_cost_std: float = 0
    total_cost_std: float = 0
    currency: str = "JPY"
    source: str = "manual"
    remarks: Optional[str] = None
    updated_at: Optional[datetime] = None

    @field_serializer("material_cost_std", "labor_cost_std", "overhead_cost_std", "total_cost_std")
    def ser_num(self, v):
        return _num(v) or 0


class ProductStandardCostDetail(ProductStandardCostListItem):
    material_lines: List[ProductStandardMaterialLineOut] = []
    labor_lines: List[ProductStandardLaborLineOut] = []
    overhead_lines: List[ProductStandardOverheadLineOut] = []


class ProductStandardCostCreate(BaseModel):
    version_id: int
    product_cd: str
    product_name: Optional[str] = None
    currency: str = "JPY"
    source: str = "manual"
    remarks: Optional[str] = None
    material_lines: List[ProductStandardMaterialLineIn] = []
    labor_lines: List[ProductStandardLaborLineIn] = []
    overhead_lines: List[ProductStandardOverheadLineIn] = []
    # 明細が空のときに直接ヘッダ金額を指定可能
    material_cost_std: Optional[Decimal] = None
    labor_cost_std: Optional[Decimal] = None
    overhead_cost_std: Optional[Decimal] = None


class ProductStandardCostUpdate(BaseModel):
    product_name: Optional[str] = None
    currency: Optional[str] = None
    source: Optional[str] = None
    remarks: Optional[str] = None
    material_lines: Optional[List[ProductStandardMaterialLineIn]] = None
    labor_lines: Optional[List[ProductStandardLaborLineIn]] = None
    overhead_lines: Optional[List[ProductStandardOverheadLineIn]] = None
    material_cost_std: Optional[Decimal] = None
    labor_cost_std: Optional[Decimal] = None
    overhead_cost_std: Optional[Decimal] = None


class ProductStandardCostListResponse(BaseModel):
    items: List[ProductStandardCostListItem]
    total: int
    page: int
    page_size: int


# --- 月次 ---

class CostAccountingPeriodCreate(BaseModel):
    year_month: str
    notes: Optional[str] = None
    status: str = "open"

    @field_validator("year_month")
    @classmethod
    def validate_year_month(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{4}-\d{2}$", v or ""):
            raise ValueError("year_month は YYYY-MM 形式で指定してください")
        return v


class CostAccountingPeriodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year_month: str
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CostPeriodProductCostIn(BaseModel):
    version_id: Optional[int] = None
    product_cd: str
    product_name: Optional[str] = None
    finished_good_qty: Decimal = Field(default=Decimal("0"))
    wip_equivalent_qty: Decimal = Field(default=Decimal("0"))
    actual_material_cost: Optional[Decimal] = None
    actual_labor_cost: Optional[Decimal] = None
    actual_overhead_cost: Optional[Decimal] = None
    variance_material_price: Decimal = Field(default=Decimal("0"))
    variance_material_qty: Decimal = Field(default=Decimal("0"))
    variance_labor_rate: Decimal = Field(default=Decimal("0"))
    variance_labor_efficiency: Decimal = Field(default=Decimal("0"))
    variance_moh_budget: Decimal = Field(default=Decimal("0"))
    variance_moh_capacity: Decimal = Field(default=Decimal("0"))
    variance_moh_efficiency: Decimal = Field(default=Decimal("0"))
    remarks: Optional[str] = None


class CostPeriodProductCostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    period_id: int
    version_id: Optional[int] = None
    product_cd: str
    product_name: Optional[str] = None
    finished_good_qty: float = 0
    wip_equivalent_qty: float = 0
    actual_material_cost: Optional[float] = None
    actual_labor_cost: Optional[float] = None
    actual_overhead_cost: Optional[float] = None
    standard_material_allowed: float = 0
    standard_labor_allowed: float = 0
    standard_overhead_allowed: float = 0
    variance_material_price: float = 0
    variance_material_qty: float = 0
    variance_labor_rate: float = 0
    variance_labor_efficiency: float = 0
    variance_moh_budget: float = 0
    variance_moh_capacity: float = 0
    variance_moh_efficiency: float = 0
    remarks: Optional[str] = None
    updated_at: Optional[datetime] = None

    # 集計差異（実際−標準許容）。実際未入力時は null 相当でフロントが非表示
    variance_material_total: Optional[float] = None
    variance_labor_total: Optional[float] = None
    variance_overhead_total: Optional[float] = None
    variance_grand_total: Optional[float] = None

    @field_serializer(
        "finished_good_qty",
        "wip_equivalent_qty",
        "actual_material_cost",
        "actual_labor_cost",
        "actual_overhead_cost",
        "standard_material_allowed",
        "standard_labor_allowed",
        "standard_overhead_allowed",
        "variance_material_price",
        "variance_material_qty",
        "variance_labor_rate",
        "variance_labor_efficiency",
        "variance_moh_budget",
        "variance_moh_capacity",
        "variance_moh_efficiency",
        "variance_material_total",
        "variance_labor_total",
        "variance_overhead_total",
        "variance_grand_total",
    )
    def ser_floats(self, v):
        return _num(v)
