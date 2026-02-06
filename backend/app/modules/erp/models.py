"""
ERP モジュールデータベースモデル
受注管理（Order）関連のモデル定義
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text, ForeignKey
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime, date


class OrderMonthly(Base):
    """月別受注管理テーブル"""
    __tablename__ = "order_monthly"

    id = Column(Integer, primary_key=True, index=True, comment="ID")
    year = Column(Integer, nullable=False, index=True, comment="年")
    month = Column(Integer, nullable=False, index=True, comment="月")
    customer_code = Column(String(50), nullable=False, index=True, comment="顧客コード")
    customer_name = Column(String(200), comment="顧客名")
    product_code = Column(String(100), nullable=False, index=True, comment="品番")
    product_name = Column(String(300), comment="品名")
    destination_code = Column(String(50), index=True, comment="納入先コード")
    destination_name = Column(String(200), comment="納入先名")
    
    # 数量情報
    forecast_units = Column(Integer, default=0, comment="内示本数")
    confirmed_units = Column(Integer, default=0, comment="確定本数")
    forecast_diff = Column(Integer, default=0, comment="内示差異")
    
    # メッキ・溶接情報
    plating_type = Column(String(50), comment="メッキ区分（社内/外注）")
    plating_count = Column(Integer, default=0, comment="メッキ数")
    welding_type = Column(String(50), comment="溶接区分（社内/外注）")
    welding_count = Column(Integer, default=0, comment="溶接数")
    
    # 単価情報
    unit_price = Column(Numeric(10, 2), comment="単価")
    total_amount = Column(Numeric(15, 2), comment="合計金額")
    
    # その他
    remarks = Column(Text, comment="備考")
    is_active = Column(Boolean, default=True, comment="有効フラグ")
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")
    created_by = Column(String(100), comment="作成者")
    updated_by = Column(String(100), comment="更新者")

    # リレーション
    daily_orders = relationship("OrderDaily", back_populates="monthly_order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OrderMonthly {self.year}/{self.month} {self.customer_code} {self.product_code}>"


class OrderDaily(Base):
    """日別受注管理テーブル"""
    __tablename__ = "order_daily"

    id = Column(Integer, primary_key=True, index=True, comment="ID")
    monthly_order_id = Column(Integer, ForeignKey("order_monthly.id", ondelete="CASCADE"), index=True, comment="月別受注ID")
    
    # 日付情報
    year = Column(Integer, nullable=False, index=True, comment="年")
    month = Column(Integer, nullable=False, index=True, comment="月")
    day = Column(Integer, nullable=False, index=True, comment="日")
    order_date = Column(Date, nullable=False, index=True, comment="受注日")
    
    # 顧客・製品情報
    customer_code = Column(String(50), nullable=False, index=True, comment="顧客コード")
    customer_name = Column(String(200), comment="顧客名")
    product_code = Column(String(100), nullable=False, index=True, comment="品番")
    product_name = Column(String(300), comment="品名")
    destination_code = Column(String(50), index=True, comment="納入先コード")
    destination_name = Column(String(200), comment="納入先名")
    
    # 数量情報
    confirmed_boxes = Column(Integer, default=0, comment="確定箱数")
    confirmed_units = Column(Integer, default=0, comment="確定本数")
    forecast_units = Column(Integer, default=0, comment="内示本数")
    shipped_boxes = Column(Integer, default=0, comment="出荷箱数")
    shipped_units = Column(Integer, default=0, comment="出荷本数")
    
    # ステータス
    shipping_status = Column(String(20), default="未出荷", comment="出荷状態（出荷済/未出荷）")
    confirmation_status = Column(String(20), default="未確認", comment="確認状態（確認済/未確認）")
    is_shipped = Column(Boolean, default=False, comment="出荷済フラグ")
    is_confirmed = Column(Boolean, default=False, comment="確認済フラグ")
    
# 単価情報
    unit_price = Column(Numeric(10, 2), comment="単価")
    total_amount = Column(Numeric(15, 2), comment="合計金額")
    
    # その他
    remarks = Column(Text, comment="備考")
    is_active = Column(Boolean, default=True, comment="有効フラグ")
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")
    created_by = Column(String(100), comment="作成者")
    updated_by = Column(String(100), comment="更新者")

    # リレーション
    monthly_order = relationship("OrderMonthly", back_populates="daily_orders")

    def __repr__(self):
        return f"<OrderDaily {self.order_date} {self.customer_code} {self.product_code}>"


class OrderLog(Base):
    """受注ログテーブル"""
    __tablename__ = "order_log"

    id = Column(Integer, primary_key=True, index=True, comment="ID")
    order_type = Column(String(20), nullable=False, index=True, comment="受注タイプ（monthly/daily）")
    order_id = Column(Integer, nullable=False, index=True, comment="受注ID")
    action = Column(String(50), nullable=False, comment="操作（create/update/delete/sync）")
    
    # 変更内容
    old_data = Column(Text, comment="変更前データ（JSON）")
    new_data = Column(Text, comment="変更後データ（JSON）")
    
    # 操作情報
    user_id = Column(Integer, comment="ユーザーID")
    user_name = Column(String(100), comment="ユーザー名")
    ip_address = Column(String(50), comment="IPアドレス")
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")

    def __repr__(self):
        return f"<OrderLog {self.order_type} {self.action} at {self.created_at}>"


class Customer(Base):
    """顧客マスタテーブル"""
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, index=True, comment="ID")
    customer_code = Column(String(50), unique=True, nullable=False, index=True, comment="顧客コード")
    customer_name = Column(String(200), nullable=False, comment="顧客名")
    customer_name_kana = Column(String(200), comment="顧客名カナ")
    
    # 連絡先情報
    postal_code = Column(String(10), comment="郵便番号")
    address = Column(String(500), comment="住所")
    phone = Column(String(20), comment="電話番号")
    fax = Column(String(20), comment="FAX番号")
    email = Column(String(100), comment="メールアドレス")
    
    # 担当者情報
    contact_person = Column(String(100), comment="担当者名")
    contact_phone = Column(String(20), comment="担当者電話番号")
    contact_email = Column(String(100), comment="担当者メール")
    
    # その他
    remarks = Column(Text, comment="備考")
    is_active = Column(Boolean, default=True, comment="有効フラグ")
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")

    def __repr__(self):
        return f"<Customer {self.customer_code} {self.customer_name}>"


class Destination(Base):
    """納入先マスタテーブル"""
    __tablename__ = "destination"

    id = Column(Integer, primary_key=True, index=True, comment="ID")
    destination_code = Column(String(50), unique=True, nullable=False, index=True, comment="納入先コード")
    destination_name = Column(String(200), nullable=False, comment="納入先名")
    destination_name_kana = Column(String(200), comment="納入先名カナ")
    
    # 顧客関連
    customer_code = Column(String(50), index=True, comment="顧客コード")
    customer_name = Column(String(200), comment="顧客名")
    
    # 住所情報
    postal_code = Column(String(10), comment="郵便番号")
    address = Column(String(500), comment="住所")
    phone = Column(String(20), comment="電話番号")
    
    # その他
    remarks = Column(Text, comment="備考")
    is_active = Column(Boolean, default=True, comment="有効フラグ")
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")

    def __repr__(self):
        return f"<Destination {self.destination_code} {self.destination_name}>"


class Product(Base):
    """製品マスタテーブル"""
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True, comment="ID")
    product_code = Column(String(100), unique=True, nullable=False, index=True, comment="品番")
    product_name = Column(String(300), nullable=False, comment="品名")
    product_name_kana = Column(String(300), comment="品名カナ")
    
    # 製品情報
    category = Column(String(100), comment="カテゴリ")
    specification = Column(Text, comment="仕様")
    unit = Column(String(20), default="個", comment="単位")
    
    # 価格情報
    standard_price = Column(Numeric(10, 2), comment="標準単価")
    cost_price = Column(Numeric(10, 2), comment="原価")
    
    # その他
    remarks = Column(Text, comment="備考")
    is_active = Column(Boolean, default=True, comment="有効フラグ")
    
    # タイムスタンプ
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")

    def __repr__(self):
        return f"<Product {self.product_code} {self.product_name}>"

