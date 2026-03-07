"""
販売管理データベースモデル
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text, ForeignKey, Index
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SalesOrder(Base):
    """受注テーブル"""
    __tablename__ = "sales_order"
    __table_args__ = (
        Index('ix_so_customer', 'customer_code'),
        Index('ix_so_date', 'order_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True, comment="受注番号")
    
    customer_code = Column(String(50), nullable=False, index=True, comment="顧客コード")
    customer_name = Column(String(200), comment="顧客名")
    
    order_date = Column(Date, nullable=False, comment="受注日")
    expected_delivery_date = Column(Date, comment="出荷予定日")
    delivery_address = Column(String(500), comment="納品先住所")
    
    # ステータス: draft, pending, approved, partial_delivered, completed, cancelled
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
    
    # 入金情報
    received_amount = Column(Numeric(15, 2), default=0, comment="入金済金額")
    payment_status = Column(String(20), default="unpaid", comment="入金状況")
    payment_term = Column(String(100), comment="支払条件")
    
    # 担当者情報
    sales_person = Column(String(100), comment="営業担当者")
    contact_person = Column(String(100), comment="連絡先担当者")
    contact_phone = Column(String(20), comment="電話番号")
    
    remarks = Column(Text, comment="備考")
    
    created_by = Column(String(100), comment="作成者")
    approved_by = Column(String(100), comment="承認者")
    approved_at = Column(DateTime, comment="承認日時")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # リレーション
    items = relationship("SalesOrderItem", back_populates="order", cascade="all, delete-orphan")


class SalesOrderItem(Base):
    """受注明細テーブル"""
    __tablename__ = "sales_order_item"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("sales_order.id", ondelete="CASCADE"), nullable=False, index=True)
    line_no = Column(Integer, nullable=False, comment="行番号")
    
    product_code = Column(String(100), nullable=False, comment="品番")
    product_name = Column(String(300), comment="品名")
    specification = Column(String(500), comment="仕様")
    unit = Column(String(20), default="個", comment="単位")
    
    quantity = Column(Integer, nullable=False, comment="受注数量")
    delivered_quantity = Column(Integer, default=0, comment="出荷済数量")
    
    unit_price = Column(Numeric(12, 2), nullable=False, comment="単価")
    tax_rate = Column(Numeric(5, 2), default=10, comment="税率")
    tax_amount = Column(Numeric(12, 2), default=0, comment="税額")
    amount = Column(Numeric(15, 2), nullable=False, comment="金額")
    
    warehouse_code = Column(String(50), comment="倉庫コード")
    expected_delivery_date = Column(Date, comment="出荷予定日")
    remarks = Column(Text, comment="備考")
    
    # リレーション
    order = relationship("SalesOrder", back_populates="items")


class SalesDelivery(Base):
    """出荷テーブル"""
    __tablename__ = "sales_delivery"

    id = Column(Integer, primary_key=True, index=True)
    delivery_no = Column(String(50), unique=True, nullable=False, index=True, comment="出荷番号")
    
    order_id = Column(Integer, ForeignKey("sales_order.id"), index=True, comment="受注ID")
    order_no = Column(String(50), comment="受注番号")
    
    customer_code = Column(String(50), nullable=False, comment="顧客コード")
    customer_name = Column(String(200), comment="顧客名")
    
    warehouse_code = Column(String(50), nullable=False, comment="倉庫コード")
    warehouse_name = Column(String(200), comment="倉庫名")
    
    delivery_date = Column(Date, nullable=False, comment="出荷日")
    delivery_address = Column(String(500), comment="納品先住所")
    
    # ステータス: draft, confirmed, shipped, completed
    status = Column(String(20), default="draft", comment="ステータス")
    
    tracking_no = Column(String(100), comment="追跡番号")
    carrier = Column(String(100), comment="運送会社")
    
    total_quantity = Column(Integer, default=0, comment="合計数量")
    remarks = Column(Text, comment="備考")
    
    created_by = Column(String(100), comment="作成者")
    confirmed_by = Column(String(100), comment="確認者")
    confirmed_at = Column(DateTime, comment="確認日時")
    shipped_at = Column(DateTime, comment="出荷日時")
    completed_at = Column(DateTime, comment="完了日時")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # リレーション
    items = relationship("SalesDeliveryItem", back_populates="delivery", cascade="all, delete-orphan")


class SalesDeliveryItem(Base):
    """出荷明細テーブル"""
    __tablename__ = "sales_delivery_item"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(Integer, ForeignKey("sales_delivery.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(Integer, comment="受注明細ID")
    
    product_code = Column(String(100), nullable=False, comment="品番")
    product_name = Column(String(300), comment="品名")
    unit = Column(String(20), default="個", comment="単位")
    
    ordered_quantity = Column(Integer, default=0, comment="受注数量")
    delivery_quantity = Column(Integer, nullable=False, comment="出荷数量")
    
    batch_no = Column(String(100), comment="ロット番号")
    remarks = Column(Text, comment="備考")
    
    # リレーション
    delivery = relationship("SalesDelivery", back_populates="items")


class SalesReturn(Base):
    """販売返品テーブル"""
    __tablename__ = "sales_return"

    id = Column(Integer, primary_key=True, index=True)
    return_no = Column(String(50), unique=True, nullable=False, index=True, comment="返品番号")
    
    order_id = Column(Integer, comment="受注ID")
    order_no = Column(String(50), comment="受注番号")
    delivery_id = Column(Integer, comment="出荷ID")
    delivery_no = Column(String(50), comment="出荷番号")
    
    customer_code = Column(String(50), nullable=False, comment="顧客コード")
    customer_name = Column(String(200), comment="顧客名")
    
    warehouse_code = Column(String(50), nullable=False, comment="倉庫コード")
    warehouse_name = Column(String(200), comment="倉庫名")
    
    return_date = Column(Date, nullable=False, comment="返品日")
    
    # ステータス: draft, pending, approved, received, completed, rejected
    status = Column(String(20), default="draft", comment="ステータス")
    
    return_reason = Column(String(500), comment="返品理由")
    total_quantity = Column(Integer, default=0, comment="合計数量")
    total_amount = Column(Numeric(15, 2), default=0, comment="合計金額")
    
    refund_status = Column(String(20), default="pending", comment="返金状況")
    refund_amount = Column(Numeric(15, 2), default=0, comment="返金額")
    
    remarks = Column(Text, comment="備考")
    
    created_by = Column(String(100), comment="作成者")
    approved_by = Column(String(100), comment="承認者")
    approved_at = Column(DateTime, comment="承認日時")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # リレーション
    items = relationship("SalesReturnItem", back_populates="sales_return", cascade="all, delete-orphan")


class SalesReturnItem(Base):
    """販売返品明細テーブル"""
    __tablename__ = "sales_return_item"

    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(Integer, ForeignKey("sales_return.id", ondelete="CASCADE"), nullable=False, index=True)
    
    product_code = Column(String(100), nullable=False, comment="品番")
    product_name = Column(String(300), comment="品名")
    unit = Column(String(20), default="個", comment="単位")
    
    return_quantity = Column(Integer, nullable=False, comment="返品数量")
    received_quantity = Column(Integer, default=0, comment="受入数量")
    
    unit_price = Column(Numeric(12, 2), comment="単価")
    amount = Column(Numeric(15, 2), comment="金額")
    
    quality_status = Column(String(20), comment="品質状況")
    return_reason = Column(String(500), comment="返品理由")
    remarks = Column(Text, comment="備考")
    
    # リレーション
    sales_return = relationship("SalesReturn", back_populates="items")
