"""
製品マスタ Pydantic スキーマ（products テーブル対応）
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class ProductBase(BaseModel):
    product_cd: str
    product_name: str
    product_type: Optional[str] = None
    location_cd: Optional[str] = None
    start_use_date: Optional[date] = None
    category: Optional[str] = None
    department_id: Optional[int] = None
    delivery_destination_cd: Optional[str] = None
    process_count: int = 1
    lead_time: Optional[int] = None
    lot_size: int = 1
    is_multistage: bool = True
    priority: int = 2
    status: str = "active"
    part_number: Optional[str] = None
    vehicle_model: Optional[str] = None
    box_type: Optional[str] = None
    unit_per_box: Optional[int] = None
    dimensions: Optional[str] = None
    weight: Optional[float] = None
    material_cd: Optional[str] = None
    cut_length: Optional[float] = None
    chamfer_length: Optional[float] = None
    developed_length: Optional[float] = None
    take_count: Optional[int] = None
    scrap_length: Optional[float] = None
    bom_id: Optional[int] = None
    route_cd: Optional[str] = None
    note: Optional[str] = None
    safety_days: Optional[int] = None
    unit_price: Optional[float] = None
    product_alias: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 材料マスタ ==========

class MaterialBase(BaseModel):
    material_cd: str
    material_name: str
    material_type: Optional[str] = None
    standard_spec: Optional[str] = None
    unit: Optional[str] = None
    diameter: Optional[float] = None
    thickness: Optional[float] = None
    length: Optional[float] = None
    supply_classification: Optional[str] = None
    pieces_per_bundle: Optional[int] = None
    usegae: Optional[str] = None
    supplier_cd: Optional[str] = None
    unit_price: Optional[float] = None
    long_weight: Optional[float] = None
    single_price: Optional[float] = None
    safety_stock: Optional[int] = 0
    lead_time: Optional[int] = None
    storage_location: Optional[str] = None
    status: int = 1
    tolerance_range: Optional[str] = None
    tolerance_1: Optional[float] = None
    tolerance_2: Optional[float] = None
    range_value: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    actual_value_1: Optional[float] = None
    actual_value_2: Optional[float] = None
    actual_value_3: Optional[float] = None
    representative_model: Optional[str] = None
    note: Optional[str] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(MaterialBase):
    pass


class MaterialResponse(MaterialBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 仕入先マスタ ==========

class SupplierBase(BaseModel):
    supplier_cd: str
    supplier_name: str
    supplier_kana: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    postal_code: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    payment_terms: Optional[str] = None
    currency: str = "JPY"
    remarks: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(SupplierBase):
    pass


class SupplierResponse(SupplierBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 工程ルートマスタ ==========

class ProcessRouteBase(BaseModel):
    route_cd: str
    route_name: str
    description: Optional[str] = None
    is_active: bool = True
    is_default: bool = False


class ProcessRouteCreate(ProcessRouteBase):
    pass


class ProcessRouteUpdate(ProcessRouteBase):
    route_cd: Optional[str] = None
    route_name: Optional[str] = None


class ProcessRouteResponse(ProcessRouteBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 工程ルートステップ（製品別） ==========

class ProcessRouteStepBase(BaseModel):
    product_cd: str
    route_cd: str
    step_no: int
    process_cd: str
    machine_id: Optional[str] = None
    standard_cycle_time: Optional[float] = None
    setup_time: Optional[float] = None
    remarks: Optional[str] = None


class ProcessRouteStepCreate(ProcessRouteStepBase):
    pass


class ProcessRouteStepUpdate(ProcessRouteStepBase):
    step_no: Optional[int] = None
    process_cd: Optional[str] = None


class ProcessRouteStepResponse(ProcessRouteStepBase):
    id: int
    process_name: Optional[str] = None  # 表示用
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
