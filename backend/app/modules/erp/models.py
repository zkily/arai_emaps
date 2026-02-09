"""
ERP モジュールデータベースモデル
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime, date


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


class OrderMonthly(Base):
    """月別受注テーブル（order_id は DB トリガーで自動採番）"""
    __tablename__ = "order_monthly"
    __table_args__ = (PrimaryKeyConstraint("id", "order_id"),)

    id = Column(Integer, autoincrement=True, comment="月订单ID")
    order_id = Column(String(50), comment="受注ID（トリガーで設定）")
    destination_cd = Column(String(50), nullable=False, index=True, comment="納入先CD")
    destination_name = Column(String(100), nullable=False, comment="納入先名")
    year = Column(Integer, nullable=False, comment="年")
    month = Column(Integer, nullable=False, comment="月")
    product_cd = Column(String(50), nullable=False, index=True, comment="製品CD")
    product_name = Column(String(100), nullable=False, comment="製品名")
    product_alias = Column(String(100), comment="製品別名")
    product_type = Column(String(20), nullable=False, default="量産品", comment="製品種別")
    forecast_units = Column(Integer, default=0, comment="内示本数")
    forecast_total_units = Column(Integer, default=0, comment="日内示合計")
    forecast_diff = Column(Integer, default=0, comment="内示差異")
    created_at = Column(DateTime, default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新日時")

    def __repr__(self):
        return f"<OrderMonthly {self.order_id} {self.destination_cd} {self.product_cd}>"

