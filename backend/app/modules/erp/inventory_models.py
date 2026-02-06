"""
在庫管理データベースモデル
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text, ForeignKey, Index
from sqlalchemy.types import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Inventory(Base):
    """在庫マスタテーブル"""
    __tablename__ = "inventory"
    __table_args__ = (
        Index('ix_inventory_product_warehouse', 'product_code', 'warehouse_code'),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(100), nullable=False, index=True, comment="品番")
    product_name = Column(String(300), comment="品名")
    warehouse_code = Column(String(50), nullable=False, index=True, comment="倉庫コード")
    warehouse_name = Column(String(200), comment="倉庫名")
    
    # 数量
    quantity = Column(Integer, default=0, comment="在庫数")
    available_quantity = Column(Integer, default=0, comment="利用可能数")
    reserved_quantity = Column(Integer, default=0, comment="予約数")
    
    # 単位・コスト
    unit = Column(String(20), default="個", comment="単位")
    unit_cost = Column(Numeric(12, 2), default=0, comment="単価")
    total_cost = Column(Numeric(15, 2), default=0, comment="在庫金額")
    
    # ロケーション
    location = Column(String(100), comment="ロケーション")
    batch_no = Column(String(100), comment="ロット番号")
    production_date = Column(Date, comment="製造日")
    expiry_date = Column(Date, comment="有効期限")
    
    # 在庫レベル
    min_stock_level = Column(Integer, default=0, comment="最小在庫レベル")
    max_stock_level = Column(Integer, default=0, comment="最大在庫レベル")
    reorder_point = Column(Integer, default=0, comment="発注点")
    
    is_active = Column(Boolean, default=True, comment="有効フラグ")
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class InventoryTransaction(Base):
    """在庫トランザクションテーブル"""
    __tablename__ = "inventory_transaction"
    __table_args__ = (
        Index('ix_inv_trans_date', 'created_at'),
        Index('ix_inv_trans_product', 'product_code'),
    )

    id = Column(Integer, primary_key=True, index=True)
    transaction_no = Column(String(50), unique=True, nullable=False, index=True, comment="取引番号")
    inventory_id = Column(Integer, ForeignKey("inventory.id"), index=True, comment="在庫ID")
    
    product_code = Column(String(100), nullable=False, index=True, comment="品番")
    product_name = Column(String(300), comment="品名")
    warehouse_code = Column(String(50), nullable=False, comment="倉庫コード")
    warehouse_name = Column(String(200), comment="倉庫名")
    
    # 取引タイプ: inbound, outbound, transfer_in, transfer_out, adjustment
    transaction_type = Column(String(30), nullable=False, comment="取引タイプ")
    
    quantity = Column(Integer, nullable=False, comment="数量")
    unit_cost = Column(Numeric(12, 2), default=0, comment="単価")
    total_cost = Column(Numeric(15, 2), default=0, comment="金額")
    
    balance_before = Column(Integer, default=0, comment="取引前残高")
    balance_after = Column(Integer, default=0, comment="取引後残高")
    
    # 参照情報
    reference_type = Column(String(50), comment="参照タイプ")
    reference_no = Column(String(100), comment="参照番号")
    reference_id = Column(Integer, comment="参照ID")
    
    batch_no = Column(String(100), comment="ロット番号")
    remarks = Column(Text, comment="備考")
    
    created_by = Column(String(100), comment="作成者")
    created_at = Column(DateTime, default=func.now(), nullable=False)


class InventoryAdjustment(Base):
    """在庫調整テーブル"""
    __tablename__ = "inventory_adjustment"

    id = Column(Integer, primary_key=True, index=True)
    adjustment_no = Column(String(50), unique=True, nullable=False, index=True, comment="調整番号")
    
    product_code = Column(String(100), nullable=False, index=True, comment="品番")
    product_name = Column(String(300), comment="品名")
    warehouse_code = Column(String(50), nullable=False, comment="倉庫コード")
    warehouse_name = Column(String(200), comment="倉庫名")
    
    # 調整タイプ: increase, decrease, stocktaking
    adjustment_type = Column(String(30), nullable=False, comment="調整タイプ")
    
    original_quantity = Column(Integer, nullable=False, comment="調整前数量")
    adjustment_quantity = Column(Integer, nullable=False, comment="調整数量")
    new_quantity = Column(Integer, nullable=False, comment="調整後数量")
    
    reason = Column(String(500), comment="調整理由")
    status = Column(String(20), default="draft", comment="ステータス")
    remarks = Column(Text, comment="備考")
    
    created_by = Column(String(100), comment="作成者")
    approved_by = Column(String(100), comment="承認者")
    approved_at = Column(DateTime, comment="承認日時")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class StockAlert(Base):
    """在庫アラートテーブル"""
    __tablename__ = "stock_alert"

    id = Column(Integer, primary_key=True, index=True)
    
    product_code = Column(String(100), nullable=False, index=True, comment="品番")
    product_name = Column(String(300), comment="品名")
    warehouse_code = Column(String(50), nullable=False, comment="倉庫コード")
    warehouse_name = Column(String(200), comment="倉庫名")
    
    # アラートタイプ: low_stock, overstock, expiring, expired
    alert_type = Column(String(30), nullable=False, comment="アラートタイプ")
    
    current_quantity = Column(Integer, comment="現在数量")
    threshold_quantity = Column(Integer, comment="しきい値")
    
    status = Column(String(20), default="active", comment="ステータス")
    remarks = Column(Text, comment="備考")
    
    handled_at = Column(DateTime, comment="対応日時")
    handled_by = Column(String(100), comment="対応者")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Warehouse(Base):
    """倉庫マスタテーブル"""
    __tablename__ = "warehouse"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_code = Column(String(50), unique=True, nullable=False, index=True, comment="倉庫コード")
    warehouse_name = Column(String(200), nullable=False, comment="倉庫名")
    
    # タイプ: material, product, semi_finished, defective, transit
    warehouse_type = Column(String(30), default="product", comment="倉庫タイプ")
    
    address = Column(String(500), comment="住所")
    manager = Column(String(100), comment="管理者")
    phone = Column(String(20), comment="電話番号")
    capacity = Column(Integer, comment="収容能力")
    
    is_active = Column(Boolean, default=True, comment="有効フラグ")
    remarks = Column(Text, comment="備考")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
