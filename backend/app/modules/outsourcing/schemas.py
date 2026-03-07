"""
外注先マスタ Pydantic スキーマ
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OutsourcingSupplierBase(BaseModel):
    supplier_cd: str
    supplier_name: str
    supplier_type: str = "plating"
    postal_code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    payment_terms: Optional[str] = None
    lead_time_days: int = 7
    remarks: Optional[str] = None
    is_active: bool = True


class OutsourcingSupplierCreate(OutsourcingSupplierBase):
    pass


class OutsourcingSupplierUpdate(BaseModel):
    supplier_cd: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_type: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    payment_terms: Optional[str] = None
    lead_time_days: Optional[int] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class OutsourcingSupplierResponse(OutsourcingSupplierBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
