"""
ERP モジュール Pydantic スキーマ
受注管理（Order）関連のスキーマ定義
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ========== 月別受注スキーマ ==========

class OrderMonthlyBase(BaseModel):
    """月別受注基本スキーマ"""
    year: int = Field(..., description="年")
    month: int = Field(..., ge=1, le=12, description="月")
    customer_code: str = Field(..., max_length=50, description="顧客コード")
    customer_name: Optional[str] = Field(None, max_length=200, description="顧客名")
    product_code: str = Field(..., max_length=100, description="品番")
    product_name: Optional[str] = Field(None, max_length=300, description="品名")
    destination_code: Optional[str] = Field(None, max_length=50, description="納入先コード")
    destination_name: Optional[str] = Field(None, max_length=200, description="納入先名")
    forecast_units: int = Field(default=0, description="内示本数")
    confirmed_units: int = Field(default=0, description="確定本数")
    forecast_diff: int = Field(default=0, description="内示差異")
    plating_type: Optional[str] = Field(None, max_length=50, description="メッキ区分")
    plating_count: int = Field(default=0, description="メッキ数")
    welding_type: Optional[str] = Field(None, max_length=50, description="溶接区分")
    welding_count: int = Field(default=0, description="溶接数")
    unit_price: Optional[Decimal] = Field(None, description="単価")
    total_amount: Optional[Decimal] = Field(None, description="合計金額")
    remarks: Optional[str] = Field(None, description="備考")


class OrderMonthlyCreate(OrderMonthlyBase):
    """月別受注作成スキーマ"""
    pass


class OrderMonthlyUpdate(BaseModel):
    """月別受注更新スキーマ"""
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    destination_code: Optional[str] = None
    destination_name: Optional[str] = None
    forecast_units: Optional[int] = None
    confirmed_units: Optional[int] = None
    forecast_diff: Optional[int] = None
    plating_type: Optional[str] = None
    plating_count: Optional[int] = None
    welding_type: Optional[str] = None
    welding_count: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    remarks: Optional[str] = None


class OrderMonthly(OrderMonthlyBase):
    """月別受注レスポンススキーマ"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# ========== 日別受注スキーマ ==========

class OrderDailyBase(BaseModel):
    """日別受注基本スキーマ"""
    year: int = Field(..., description="年")
    month: int = Field(..., ge=1, le=12, description="月")
    day: int = Field(..., ge=1, le=31, description="日")
    order_date: date = Field(..., description="受注日")
    customer_code: str = Field(..., max_length=50, description="顧客コード")
    customer_name: Optional[str] = Field(None, max_length=200, description="顧客名")
    product_code: str = Field(..., max_length=100, description="品番")
    product_name: Optional[str] = Field(None, max_length=300, description="品名")
    destination_code: Optional[str] = Field(None, max_length=50, description="納入先コード")
    destination_name: Optional[str] = Field(None, max_length=200, description="納入先名")
    confirmed_boxes: int = Field(default=0, description="確定箱数")
    confirmed_units: int = Field(default=0, description="確定本数")
    forecast_units: int = Field(default=0, description="内示本数")
    shipped_boxes: int = Field(default=0, description="出荷箱数")
    shipped_units: int = Field(default=0, description="出荷本数")
    shipping_status: str = Field(default="未出荷", description="出荷状態")
    confirmation_status: str = Field(default="未確認", description="確認状態")
    unit_price: Optional[Decimal] = Field(None, description="単価")
    total_amount: Optional[Decimal] = Field(None, description="合計金額")
    remarks: Optional[str] = Field(None, description="備考")


class OrderDailyCreate(OrderDailyBase):
    """日別受注作成スキーマ"""
    monthly_order_id: Optional[int] = None


class OrderDailyUpdate(BaseModel):
    """日別受注更新スキーマ"""
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    destination_code: Optional[str] = None
    destination_name: Optional[str] = None
    confirmed_boxes: Optional[int] = None
    confirmed_units: Optional[int] = None
    forecast_units: Optional[int] = None
    shipped_boxes: Optional[int] = None
    shipped_units: Optional[int] = None
    shipping_status: Optional[str] = None
    confirmation_status: Optional[str] = None
    unit_price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    remarks: Optional[str] = None


class OrderDaily(OrderDailyBase):
    """日別受注レスポンススキーマ"""
    id: int
    monthly_order_id: Optional[int] = None
    is_shipped: bool
    is_confirmed: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


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


# ========== ログスキーマ ==========

class OrderLog(BaseModel):
    """受注ログスキーマ"""
    id: int
    order_type: str
    order_id: int
    action: str
    old_data: Optional[str] = None
    new_data: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 統計・集計スキーマ ==========

class OrderMonthlySummary(BaseModel):
    """月別受注集計スキーマ"""
    forecast_units: int = Field(default=0, description="内示本数合計")
    confirmed_units: int = Field(default=0, description="確定本数合計")
    forecast_total_units: int = Field(default=0, description="内示合計")
    forecast_diff: int = Field(default=0, description="内示差異")
    plating_count: int = Field(default=0, description="社内メッキ数")
    external_plating_count: int = Field(default=0, description="外注メッキ数")
    internal_welding_count: int = Field(default=0, description="社内溶接数")
    external_welding_count: int = Field(default=0, description="外注溶接数")


class OrderDailySummary(BaseModel):
    """日別受注集計スキーマ"""
    total_confirmed_boxes: int = Field(default=0, description="確定箱数合計")
    total_confirmed_units: int = Field(default=0, description="確定本数合計")
    total_forecast_units: int = Field(default=0, description="内示本数合計")
    shipped_orders_count: int = Field(default=0, description="出荷済件数")
    unshipped_orders_count: int = Field(default=0, description="未出荷件数")
    confirmed_orders_count: int = Field(default=0, description="確認済件数")
    unconfirmed_orders_count: int = Field(default=0, description="未確認件数")


# ========== 一括操作スキーマ ==========

class BatchConfirmRequest(BaseModel):
    """一括確認リクエストスキーマ"""
    order_ids: List[int] = Field(..., description="受注IDリスト")


class BatchImportRequest(BaseModel):
    """一括インポートリクエストスキーマ"""
    data: List[OrderDailyCreate] = Field(..., description="受注データリスト")


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

