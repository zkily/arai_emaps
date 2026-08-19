"""備品購入：仕入先別カタログ / 発注ヘッダ・明細"""
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class SupplyItem(Base):
    """備品マスタ（仕入先別カタログ）"""

    __tablename__ = "supply_items"
    __table_args__ = (UniqueConstraint("supplier_cd", "item_cd", name="uk_supply_item_supplier"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_cd = Column(String(50), nullable=False, index=True, comment="備品CD")
    item_name = Column(String(200), nullable=False, comment="備品名")
    specification = Column(String(200), comment="規格")
    unit = Column(String(20), nullable=False, default="個", comment="単位")
    pack_qty = Column(Integer, nullable=False, default=1, comment="個数（入り数）")
    order_lot = Column(Integer, nullable=False, default=1, comment="注文ロット")
    unit_price = Column(Numeric(12, 2), nullable=False, default=0, comment="単価")
    supplier_cd = Column(String(50), nullable=False, index=True, comment="仕入先CD")
    is_discontinued = Column(Boolean, nullable=False, default=False, index=True, comment="終息")
    remarks = Column(Text, comment="備考")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(50))


class SupplyPurchaseOrder(Base):
    """備品発注ヘッダ"""

    __tablename__ = "supply_purchase_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(30), unique=True, nullable=False, index=True, comment="発注番号")
    order_date = Column(Date, nullable=False, index=True, comment="発注日")
    delivery_date = Column(Date, comment="納入日")
    supplier_cd = Column(String(50), nullable=False, index=True, comment="仕入先CD")
    supplier_name = Column(String(100), comment="仕入先名")
    status = Column(String(20), nullable=False, default="ordered", index=True)
    total_amount = Column(Numeric(14, 2), nullable=False, default=0, comment="合計金額")
    remarks = Column(Text)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SupplyPurchaseOrderLine(Base):
    """備品発注明細（発注時点の単価・規格をスナップショット）"""

    __tablename__ = "supply_purchase_order_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(
        Integer,
        ForeignKey("supply_purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_no = Column(Integer, nullable=False, default=1)
    item_cd = Column(String(50), nullable=False)
    item_name = Column(String(200))
    specification = Column(String(200))
    unit = Column(String(20), default="個")
    pack_qty = Column(Integer, nullable=False, default=1)
    order_lot = Column(Integer, nullable=False, default=1)
    order_qty = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    amount = Column(Numeric(14, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=func.now())
