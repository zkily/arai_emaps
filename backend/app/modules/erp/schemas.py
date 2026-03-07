"""
ERP モジュール Pydantic スキーマ
"""
from pydantic import BaseModel, Field, validator, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date as date_type
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
    forecast_total_units: int = Field(default=0, ge=0, description="確定本数")
    forecast_diff: int = Field(default=0, description="内示差異（確定本数-内示本数）")


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
    """月別受注レスポンススキーマ。内示差異は常に 確定本数 - 内示本数 で返す。"""
    id: int
    order_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def compute_forecast_diff(self) -> "OrderMonthly":
        """返却時に内示差異 = 確定本数 - 内示本数 で上書き（DB に旧公式で入っているデータを補正）"""
        self.forecast_diff = (self.forecast_total_units or 0) - (self.forecast_units or 0)
        return self


# ========== 日別受注スキーマ ==========

def _coerce_int_zero(v):
    """DB で NULL の数値カラムを 0 に正規化"""
    return 0 if v is None else v


class OrderDailyBase(BaseModel):
    """日別受注基本スキーマ"""
    monthly_order_id: Optional[str] = Field(None, max_length=50, description="月订单ID")
    destination_cd: str = Field(..., max_length=50, description="納入先CD")
    destination_name: Optional[str] = Field(None, max_length=100, description="納入先名")
    date: date_type = Field(..., description="年月日")
    weekday: Optional[str] = Field(None, max_length=10, description="曜日")
    product_cd: str = Field(..., max_length=50, description="製品CD")
    product_name: Optional[str] = Field(None, max_length=100, description="製品名")
    product_alias: Optional[str] = Field(None, max_length=100, description="製品別名")
    forecast_units: int = Field(default=0, ge=0, description="内示本数")
    confirmed_boxes: int = Field(default=0, ge=0, description="確定箱数")
    confirmed_units: int = Field(default=0, ge=0, description="確定本数")
    status: Optional[str] = Field(default="未出荷", max_length=50, description="日別受注ステータス")
    remarks: Optional[str] = Field(default="", max_length=255, description="備考")
    unit_per_box: int = Field(default=0, ge=0, description="1箱あたりの個数")
    batch_id: Optional[int] = None
    batch_no: Optional[str] = Field(None, max_length=50)
    supply_status: Optional[str] = Field(None, max_length=20)
    fulfilled_from_stock: int = Field(default=0, ge=0)
    fulfilled_from_wip: int = Field(default=0, ge=0)
    product_type: Optional[str] = Field(None, max_length=20)
    confirmed: bool = Field(default=False, description="是否已确认")
    confirmed_by: Optional[str] = Field(None, max_length=50)
    confirmed_at: Optional[datetime] = None
    delivery_date: Optional[date_type] = Field(None, description="納入日")
    shipping_no: Optional[str] = Field(None, max_length=50)

    @field_validator(
        "forecast_units", "confirmed_boxes", "confirmed_units",
        "unit_per_box", "fulfilled_from_stock", "fulfilled_from_wip",
        mode="before",
    )
    @classmethod
    def coerce_int_null_to_zero(cls, v):
        return _coerce_int_zero(v)

    @field_validator("confirmed", mode="before")
    @classmethod
    def coerce_confirmed_null_to_false(cls, v):
        return False if v is None else bool(v)


class OrderDailyCreate(OrderDailyBase):
    """日別受注作成"""
    pass


class OrderDailyUpdate(BaseModel):
    """日別受注更新スキーマ"""
    monthly_order_id: Optional[str] = None
    destination_cd: Optional[str] = None
    destination_name: Optional[str] = None
    date: Optional[date_type] = None
    weekday: Optional[str] = None
    product_cd: Optional[str] = None
    product_name: Optional[str] = None
    product_alias: Optional[str] = None
    forecast_units: Optional[int] = Field(None, ge=0)
    confirmed_boxes: Optional[int] = Field(None, ge=0)
    confirmed_units: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    remarks: Optional[str] = None
    unit_per_box: Optional[int] = Field(None, ge=0)
    batch_id: Optional[int] = None
    batch_no: Optional[str] = None
    supply_status: Optional[str] = None
    fulfilled_from_stock: Optional[int] = Field(None, ge=0)
    fulfilled_from_wip: Optional[int] = Field(None, ge=0)
    product_type: Optional[str] = None
    confirmed: Optional[bool] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    delivery_date: Optional[date_type] = None
    shipping_no: Optional[str] = None


class OrderDaily(OrderDailyBase):
    """日別受注レスポンススキーマ"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 一括操作スキーマ ==========

class BatchUpdateDailyItem(BaseModel):
    """日別受注一括更新の1件"""
    id: int
    forecast_units: Optional[int] = Field(None, ge=0)
    confirmed_boxes: Optional[int] = Field(None, ge=0)
    confirmed_units: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    remarks: Optional[str] = None


class BatchUpdateDailyRequest(BaseModel):
    """日別受注一括更新リクエスト"""
    list: List[BatchUpdateDailyItem]


class SyncRequest(BaseModel):
    """同期リクエストスキーマ"""
    sync_date: Optional[date_type] = Field(None, description="同期対象日（未指定の場合は今日）")


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

