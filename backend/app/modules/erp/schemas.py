"""
ERP モジュール Pydantic スキーマ
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ========== 顧客スキーマ ==========

class CustomerBase(BaseModel):
    """顧客基本スキーマ"""
    customer_code: str = Field(..., max_length=50, description="顧客コード")
    customer_name: str = Field(..., max_length=200, description="顧客名")
    customer_name_kana: Optional[str] = Field(None, max_length=200, description="顧客名カナ")
    postal_code: Optional[str] = Field(None, max_length=10, description="郵便番号")
    address: Optional[str] = Field(None, max_length=500, description="住所")
    phone: Optional[str] = Field(None, max_length=20, description="電話番号")
    fax: Optional[str] = Field(None, max_length=20, description="FAX番号")
    email: Optional[str] = Field(None, max_length=100, description="メールアドレス")
    contact_person: Optional[str] = Field(None, max_length=100, description="担当者名")
    contact_phone: Optional[str] = Field(None, max_length=20, description="担当者電話番号")
    contact_email: Optional[str] = Field(None, max_length=100, description="担当者メール")
    remarks: Optional[str] = Field(None, description="備考")


class CustomerCreate(CustomerBase):
    """顧客作成スキーマ"""
    pass


class CustomerUpdate(BaseModel):
    """顧客更新スキーマ"""
    customer_name: Optional[str] = None
    customer_name_kana: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    remarks: Optional[str] = None


class Customer(CustomerBase):
    """顧客レスポンススキーマ"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 納入先スキーマ ==========

class DestinationBase(BaseModel):
    """納入先基本スキーマ"""
    destination_code: str = Field(..., max_length=50, description="納入先コード")
    destination_name: str = Field(..., max_length=200, description="納入先名")
    destination_name_kana: Optional[str] = Field(None, max_length=200, description="納入先名カナ")
    customer_code: Optional[str] = Field(None, max_length=50, description="顧客コード")
    customer_name: Optional[str] = Field(None, max_length=200, description="顧客名")
    postal_code: Optional[str] = Field(None, max_length=10, description="郵便番号")
    address: Optional[str] = Field(None, max_length=500, description="住所")
    phone: Optional[str] = Field(None, max_length=20, description="電話番号")
    remarks: Optional[str] = Field(None, description="備考")


class DestinationCreate(DestinationBase):
    """納入先作成スキーマ"""
    pass


class DestinationUpdate(BaseModel):
    """納入先更新スキーマ"""
    destination_name: Optional[str] = None
    destination_name_kana: Optional[str] = None
    customer_code: Optional[str] = None
    customer_name: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    remarks: Optional[str] = None


class Destination(DestinationBase):
    """納入先レスポンススキーマ"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 製品スキーマ ==========

class ProductBase(BaseModel):
    """製品基本スキーマ"""
    product_code: str = Field(..., max_length=100, description="品番")
    product_name: str = Field(..., max_length=300, description="品名")
    product_name_kana: Optional[str] = Field(None, max_length=300, description="品名カナ")
    category: Optional[str] = Field(None, max_length=100, description="カテゴリ")
    specification: Optional[str] = Field(None, description="仕様")
    unit: str = Field(default="個", max_length=20, description="単位")
    standard_price: Optional[Decimal] = Field(None, description="標準単価")
    cost_price: Optional[Decimal] = Field(None, description="原価")
    remarks: Optional[str] = Field(None, description="備考")


class ProductCreate(ProductBase):
    """製品作成スキーマ"""
    pass


class ProductUpdate(BaseModel):
    """製品更新スキーマ"""
    product_name: Optional[str] = None
    product_name_kana: Optional[str] = None
    category: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    standard_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    remarks: Optional[str] = None


class Product(ProductBase):
    """製品レスポンススキーマ"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 月別受注スキーマ ==========

class OrderMonthlyBase(BaseModel):
    """月別受注基本スキーマ"""
    destination_cd: str = Field(..., max_length=50, description="納入先CD")
    destination_name: str = Field(..., max_length=100, description="納入先名")
    year: int = Field(..., description="年")
    month: int = Field(..., ge=1, le=12, description="月")
    product_cd: str = Field(..., max_length=50, description="製品CD")
    product_name: str = Field(..., max_length=100, description="製品名")
    product_alias: Optional[str] = Field(None, max_length=100, description="製品別名")
    product_type: str = Field(default="量産品", max_length=20, description="製品種別")
    forecast_units: int = Field(default=0, ge=0, description="内示本数")
    forecast_total_units: int = Field(default=0, ge=0, description="日内示合計")
    forecast_diff: int = Field(default=0, description="内示差異")


class OrderMonthlyCreate(OrderMonthlyBase):
    """月別受注作成（order_id はトリガーで自動採番）"""
    pass


class OrderMonthlyUpdate(BaseModel):
    """月別受注更新スキーマ"""
    destination_cd: Optional[str] = Field(None, max_length=50)
    destination_name: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    product_cd: Optional[str] = Field(None, max_length=50)
    product_name: Optional[str] = Field(None, max_length=100)
    product_alias: Optional[str] = Field(None, max_length=100)
    product_type: Optional[str] = Field(None, max_length=20)
    forecast_units: Optional[int] = Field(None, ge=0)
    forecast_total_units: Optional[int] = Field(None, ge=0)
    forecast_diff: Optional[int] = None


class OrderMonthly(OrderMonthlyBase):
    """月別受注レスポンススキーマ"""
    id: int
    order_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 一括操作スキーマ ==========

class SyncRequest(BaseModel):
    """同期リクエストスキーマ"""
    sync_date: Optional[date] = Field(None, description="同期対象日（未指定の場合は今日）")


# ========== ページネーションスキーマ ==========

class PaginationParams(BaseModel):
    """ページネーションパラメータ"""
    page: int = Field(default=1, ge=1, description="ページ番号")
    page_size: int = Field(default=50, ge=1, le=1000, description="ページサイズ")


class PaginatedResponse(BaseModel):
    """ページネーションレスポンス"""
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="現在のページ")
    page_size: int = Field(..., description="ページサイズ")
    total_pages: int = Field(..., description="総ページ数")
    items: List = Field(..., description="データリスト")

