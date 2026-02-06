"""
購買管理データベースモデル
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text, ForeignKey, Index
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PurchaseOrder(Base):
    """発注テーブル"""
    __tablename__ = "purchase_order"
    __table_args__ = (
        Index('ix_po_supplier', 'supplier_code'),
        Index('ix_po_date', 'order_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True, comment="発注番号")
    
    supplier_code = Column(String(50), nullable=False, index=True, comment="仕入先コード")
    supplier_name = Column(String(200), comment="仕入先名")
    
    order_date = Column(Date, nullable=False, comment="発注日")
    expected_delivery_date = Column(Date, comment="入荷予定日")
    
    warehouse_code = Column(String(50), comment="入荷倉庫コード")
    warehouse_name = Column(String(200), comment="入荷倉庫名")
    
    # ステータス: draft, pending, approved, partial_received, completed, cancelled
    status = Column(String(30), default="draft", comment="ステータス")
    
    # 金額情報
    currency = Column(String(10), default="JPY", comment="通貨")
    exchange_rate = Column(Numeric(10, 4), default=1, comment="為替レート")
    subtotal = Column(Numeric(15, 2), default=0, comment="小計")
    tax_rate = Column(Numeric(5, 2), default=10, comment="税率")
    tax_amount = Column(Numeric(15, 2), default=0, comment="税額")
    discount_rate = Column(Numeric(5, 2), default=0, comment="割引率")
    discount_amount = Column(Numeric(15, 2), default=0, comment="割引額")
    total_amount = Column(Numeric(15, 2), default=0, comment="合計金額")
    
    # 支払情報
    paid_amount = Column(Numeric(15, 2), default=0, comment="支払済金額")
    payment_status = Column(String(20), default="unpaid", comment="支払状況")
    payment_term = Column(String(100), comment="支払条件")
    
    # 連絡先
    contact_person = Column(String(100), comment="担当者")
    contact_phone = Column(String(20), comment="電話番号")
    delivery_address = Column(String(500), comment="納品先住所")
    
    remarks = Column(Text, comment="備考")
    
    created_by = Column(String(100), comment="作成者")
    approved_by = Column(String(100), comment="承認者")
    approved_at = Column(DateTime, comment="承認日時")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # リレーション
    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    """発注明細テーブル"""
    __tablename__ = "purchase_order_item"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("purchase_order.id", ondelete="CASCADE"), nullable=False, index=True)
    line_no = Column(Integer, nullable=False, comment="行番号")
    
    product_code = Column(String(100), nullable=False, comment="品番")
    product_name = Column(String(300), comment="品名")
    specification = Column(String(500), comment="仕様")
    unit = Column(String(20), default="個", comment="単位")
    
    quantity = Column(Integer, nullable=False, comment="発注数量")
    received_quantity = Column(Integer, default=0, comment="入荷済数量")
    
    unit_price = Column(Numeric(12, 2), nullable=False, comment="単価")
    tax_rate = Column(Numeric(5, 2), default=10, comment="税率")
    tax_amount = Column(Numeric(12, 2), default=0, comment="税額")
    amount = Column(Numeric(15, 2), nullable=False, comment="金額")
    
    expected_delivery_date = Column(Date, comment="入荷予定日")
    remarks = Column(Text, comment="備考")
    
    # リレーション
    order = relationship("PurchaseOrder", back_populates="items")


class PurchaseReceipt(Base):
    """入荷テーブル"""
    __tablename__ = "purchase_receipt"

    id = Column(Integer, primary_key=True, index=True)
    receipt_no = Column(String(50), unique=True, nullable=False, index=True, comment="入荷番号")
    
    order_id = Column(Integer, ForeignKey("purchase_order.id"), index=True, comment="発注ID")
    order_no = Column(String(50), comment="発注番号")
    
    supplier_code = Column(String(50), nullable=False, comment="仕入先コード")
    supplier_name = Column(String(200), comment="仕入先名")
    
    warehouse_code = Column(String(50), nullable=False, comment="倉庫コード")
    warehouse_name = Column(String(200), comment="倉庫名")
    
    receipt_date = Column(Date, nullable=False, comment="入荷日")
    status = Column(String(20), default="draft", comment="ステータス")
    
    total_quantity = Column(Integer, default=0, comment="合計数量")
    remarks = Column(Text, comment="備考")
    
    created_by = Column(String(100), comment="作成者")
    confirmed_by = Column(String(100), comment="確認者")
    confirmed_at = Column(DateTime, comment="確認日時")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # リレーション
    items = relationship("PurchaseReceiptItem", back_populates="receipt", cascade="all, delete-orphan")


class PurchaseReceiptItem(Base):
    """入荷明細テーブル"""
    __tablename__ = "purchase_receipt_item"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("purchase_receipt.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(Integer, comment="発注明細ID")
    
    product_code = Column(String(100), nullable=False, comment="品番")
    product_name = Column(String(300), comment="品名")
    unit = Column(String(20), default="個", comment="単位")
    
    ordered_quantity = Column(Integer, default=0, comment="発注数量")
    received_quantity = Column(Integer, nullable=False, comment="入荷数量")
    
    location = Column(String(100), comment="ロケーション")
    batch_no = Column(String(100), comment="ロット番号")
    production_date = Column(Date, comment="製造日")
    expiry_date = Column(Date, comment="有効期限")
    
    remarks = Column(Text, comment="備考")
    
    # リレーション
    receipt = relationship("PurchaseReceipt", back_populates="items")


class Supplier(Base):
    """仕入先マスタテーブル"""
    __tablename__ = "supplier"

    id = Column(Integer, primary_key=True, index=True)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True, comment="仕入先コード")
    supplier_name = Column(String(200), nullable=False, comment="仕入先名")
    supplier_name_kana = Column(String(200), comment="仕入先名カナ")
    
    # タイプ: manufacturer, distributor, service, other
    supplier_type = Column(String(30), default="manufacturer", comment="仕入先タイプ")
    category = Column(String(100), comment="カテゴリ")
    
    tax_id = Column(String(50), comment="税務番号")
    postal_code = Column(String(10), comment="郵便番号")
    address = Column(String(500), comment="住所")
    phone = Column(String(20), comment="電話番号")
    fax = Column(String(20), comment="FAX番号")
    email = Column(String(100), comment="メールアドレス")
    website = Column(String(200), comment="ウェブサイト")
    
    # 銀行情報
    bank_name = Column(String(100), comment="銀行名")
    bank_branch = Column(String(100), comment="支店名")
    bank_account_type = Column(String(20), comment="口座種別")
    bank_account_no = Column(String(50), comment="口座番号")
    bank_account_name = Column(String(100), comment="口座名義")
    
    payment_term = Column(String(100), comment="支払条件")
    currency = Column(String(10), default="JPY", comment="通貨")
    credit_limit = Column(Numeric(15, 2), comment="与信限度額")
    
    rating = Column(String(1), comment="評価")
    
    is_active = Column(Boolean, default=True, comment="有効フラグ")
    remarks = Column(Text, comment="備考")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class SupplierContact(Base):
    """仕入先連絡先テーブル"""
    __tablename__ = "supplier_contact"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("supplier.id", ondelete="CASCADE"), nullable=False, index=True)
    
    contact_name = Column(String(100), nullable=False, comment="連絡先名")
    department = Column(String(100), comment="部署")
    position = Column(String(100), comment="役職")
    phone = Column(String(20), comment="電話番号")
    mobile = Column(String(20), comment="携帯電話")
    email = Column(String(100), comment="メールアドレス")
    
    is_primary = Column(Boolean, default=False, comment="主要連絡先フラグ")
    remarks = Column(Text, comment="備考")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
