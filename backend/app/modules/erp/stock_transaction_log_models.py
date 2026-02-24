"""
在庫取引履歴 (stock_transaction_logs) モデル
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.types import Numeric
from app.core.database import Base


class StockTransactionLog(Base):
    """在庫受払履歴テーブル"""
    __tablename__ = "stock_transaction_logs"
    __table_args__ = (
        Index('idx_target_time', 'target_cd', 'transaction_time'),
        Index('idx_location_target', 'location_cd', 'target_cd'),
        Index('idx_lot', 'lot_no', 'target_cd'),
        Index('idx_order', 'order_no'),
        Index('idx_source_file', 'source_file'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="在庫操作履歴ID")
    stock_type = Column(String(20), nullable=False, comment="在庫種別 (製品,材料,部品,仕掛品)")
    transaction_type = Column(String(20), nullable=False, comment="操作種別")
    target_cd = Column(String(50), nullable=False, index=True, comment="品目コード")
    location_cd = Column(String(50), nullable=False, index=True, comment="保管場所コード")
    lot_no = Column(String(50), nullable=True, comment="ロット番号")
    process_cd = Column(String(50), nullable=True, comment="工程コード")
    machine_cd = Column(String(50), nullable=True, comment="設備コード")
    quantity = Column(Numeric(18, 4), nullable=False, comment="操作数量")
    unit = Column(String(10), nullable=True, comment="単位")
    order_no = Column(String(50), nullable=True, comment="関連伝票No")
    notes = Column(String(100), nullable=True, comment="注文番号等（トリガー互換・削除照合用）")
    related_log_id = Column(BigInteger, nullable=True, comment="取消時の元ログIDなど")
    operator_id = Column(String(50), nullable=True, comment="操作担当者ID")
    operator_name = Column(String(100), nullable=True, comment="担当者名")
    transaction_time = Column(DateTime, nullable=False, comment="操作日時")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="レコード作成日時")
    source_file = Column(String(100), nullable=True, comment="来源文件名（监听文件时写入文件名，否则如手入力等）")
    remarks = Column(Text, nullable=True, comment="備考")
