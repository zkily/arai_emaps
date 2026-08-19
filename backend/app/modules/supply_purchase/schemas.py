"""備品購入 Pydantic スキーマ"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SupplyItemBase(BaseModel):
    item_cd: str = Field(..., min_length=1, max_length=50)
    item_name: str = Field(..., min_length=1, max_length=200)
    specification: Optional[str] = None
    unit: str = "個"
    pack_qty: int = Field(1, ge=1)
    order_lot: int = Field(1, ge=1)
    unit_price: Decimal = Field(Decimal("0"), ge=0)
    supplier_cd: str = Field(..., min_length=1, max_length=50)
    is_discontinued: bool = False
    remarks: Optional[str] = None


class SupplyItemCreate(SupplyItemBase):
    pass


class SupplyItemUpdate(BaseModel):
    item_cd: Optional[str] = Field(None, min_length=1, max_length=50)
    item_name: Optional[str] = Field(None, min_length=1, max_length=200)
    specification: Optional[str] = None
    unit: Optional[str] = None
    pack_qty: Optional[int] = Field(None, ge=1)
    order_lot: Optional[int] = Field(None, ge=1)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    is_discontinued: Optional[bool] = None
    supplier_cd: Optional[str] = Field(None, min_length=1, max_length=50)
    remarks: Optional[str] = None


class SupplyOrderLineIn(BaseModel):
    item_id: int
    order_qty: int = Field(..., ge=1)


class SupplyOrderCreate(BaseModel):
    supplier_cd: str = Field(..., min_length=1, max_length=50)
    order_date: date
    delivery_date: Optional[date] = None
    remarks: Optional[str] = None
    lines: list[SupplyOrderLineIn] = Field(..., min_length=1)
