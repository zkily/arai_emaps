"""部品購買 Pydantic スキーマ"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class PartStockBase(BaseModel):
    part_cd: str
    part_name: str
    date: date
    initial_stock: Optional[int] = 0
    current_stock: Optional[int] = 0
    planned_usage: Optional[int] = 0
    usage_plan_qty: Optional[int] = 0
    stock_trend: Optional[int] = 0
    adjustment_quantity: Optional[int] = 0
    standard_spec: Optional[str] = ""
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    pieces_per_bundle: Optional[int] = 0
    supplier_cd: Optional[str] = None
    supplier_name: Optional[str] = None
    lead_time: Optional[int] = 0
    order_quantity: Optional[int] = 0
    order_bundle_quantity: Optional[int] = 0
    order_amount: Optional[Decimal] = None
    remarks: Optional[str] = ""


class PartStockCreate(PartStockBase):
    pass


class PartStockUpdate(BaseModel):
    part_cd: Optional[str] = None
    part_name: Optional[str] = None
    date: Optional[date] = None
    initial_stock: Optional[int] = None
    current_stock: Optional[int] = None
    planned_usage: Optional[int] = None
    usage_plan_qty: Optional[int] = None
    stock_trend: Optional[int] = None
    adjustment_quantity: Optional[int] = None
    standard_spec: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    pieces_per_bundle: Optional[int] = None
    supplier_cd: Optional[str] = None
    supplier_name: Optional[str] = None
    lead_time: Optional[int] = None
    order_quantity: Optional[int] = None
    order_bundle_quantity: Optional[int] = None
    order_amount: Optional[Decimal] = None
    remarks: Optional[str] = None


class PartStockResponse(PartStockBase):
    id: int
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PartStockCalculateRequest(BaseModel):
    """在庫計算: 使用数・使用計画の同期期間。start_date/end_date を両方指定したときのみその区間を採用。片方のみは無視。"""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
