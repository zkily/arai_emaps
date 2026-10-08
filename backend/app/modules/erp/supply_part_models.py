"""補給品在庫台帳モデル"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.core.database import Base


class SupplyPartLocation(Base):
    __tablename__ = "supply_part_locations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    name = Column(String(100), nullable=False, unique=True, comment="保管場所名")
    sort_order = Column(Integer, nullable=False, default=0, comment="表示順")
    is_active = Column(Boolean, nullable=False, default=True, comment="使用フラグ")
    note = Column(String(255), nullable=True, comment="備考")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="作成日時")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新日時"
    )


class SupplyPartStock(Base):
    __tablename__ = "supply_part_stocks"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    product_cd = Column(String(50), nullable=False, unique=True, comment="品番")
    product_name = Column(String(200), nullable=False, comment="品名")
    product_alias = Column(String(100), nullable=True, comment="製品別名")
    part_number = Column(String(50), nullable=True, comment="品番（かんばん）")
    destination_cd = Column(String(50), nullable=True, comment="納入先CD")
    destination_name = Column(String(100), nullable=True, comment="納入先名")
    storage_location = Column(String(100), nullable=False, default="", comment="保管場所")
    shelf_no = Column(String(50), nullable=True, comment="棚番")
    keeper = Column(String(50), nullable=True, comment="担当")
    safety_stock = Column(Integer, nullable=False, default=0, comment="安全在庫")
    on_hand_qty = Column(Integer, nullable=False, default=0, comment="現在庫")
    next_production_date = Column(Date, nullable=True, comment="次回生産予定日")
    next_production_qty = Column(Integer, nullable=False, default=0, comment="生産予定数量")
    quality_status = Column(String(20), nullable=False, default="良好", comment="品質状態")
    note = Column(Text, nullable=True, comment="備考")
    source = Column(String(20), nullable=False, comment="登録元（transfer/manual）")
    created_by_user_id = Column(Integer, nullable=True, comment="登録者ID")
    updated_by_user_id = Column(Integer, nullable=True, comment="更新者ID")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="作成日時")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新日時"
    )


class SupplyPartTransaction(Base):
    __tablename__ = "supply_part_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    stock_id = Column(
        BigInteger,
        ForeignKey("supply_part_stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="在庫カードID",
    )
    product_cd = Column(String(50), nullable=False, index=True, comment="品番")
    txn_type = Column(String(20), nullable=False, comment="取引区分")
    quantity = Column(
        Integer, nullable=False, default=0, comment="数量（入庫プラス、出庫マイナス）"
    )
    balance_after = Column(Integer, nullable=False, default=0, comment="発生後残高")
    occurred_date = Column(Date, nullable=False, comment="発生日")
    note = Column(Text, nullable=True, comment="備考")
    created_by_user_id = Column(Integer, nullable=True, comment="登録者ID")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="作成日時")
