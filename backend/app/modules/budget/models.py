"""予算管理テーブルモデル"""
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.core.database import Base


class BudgetImportBatch(Base):
    """予算CSV取込バッチ"""

    __tablename__ = "budget_import_batches"
    __table_args__ = {"mysql_comment": "予算CSV取込バッチ"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    months_json = Column(Text)
    total_rows = Column(Integer, nullable=False, default=0)
    matched_rows = Column(Integer, nullable=False, default=0)
    unmatched_rows = Column(Integer, nullable=False, default=0)
    inserted_rows = Column(Integer, nullable=False, default=0)
    updated_rows = Column(Integer, nullable=False, default=0)
    uploaded_by = Column(String(100))
    remark = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())


class BudgetMonthly(Base):
    """月次予算数量（同月・同品番は上書き）"""

    __tablename__ = "budget_monthly"
    __table_args__ = {"mysql_comment": "月次予算数量"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    year = Column(SmallInteger, nullable=False, index=True)
    month = Column(SmallInteger, nullable=False)
    development_code = Column(String(100))
    part_number = Column(String(50), nullable=False, index=True)
    product_cd = Column(String(50), index=True)
    product_name = Column(String(100))
    budget_qty = Column(Integer, nullable=False, default=0)
    match_status = Column(String(20), nullable=False, default="unmatched")
    import_batch_id = Column(BigInteger, ForeignKey("budget_import_batches.id", ondelete="SET NULL"))
    source_file_name = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BudgetWorkingDays(Base):
    """月次稼働日数（共通デフォルト。日平均 = 予算数量 ÷ 稼働日数）"""

    __tablename__ = "budget_working_days"
    __table_args__ = {"mysql_comment": "予算分析用 月次稼働日数（共通）"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    year = Column(SmallInteger, nullable=False, index=True)
    month = Column(SmallInteger, nullable=False)
    working_days = Column(Integer, nullable=False, default=0)
    remark = Column(String(255))
    updated_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BudgetProcessWorkingDays(Base):
    """工程別月次稼働日数（未設定時は共通稼働日を使用）"""

    __tablename__ = "budget_process_working_days"
    __table_args__ = {"mysql_comment": "予算分析用 工程別月次稼働日数"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    year = Column(SmallInteger, nullable=False, index=True)
    month = Column(SmallInteger, nullable=False)
    process_cd = Column(String(50), nullable=False, index=True)
    process_name = Column(String(100))
    working_days = Column(Integer, nullable=False, default=0)
    remark = Column(String(255))
    updated_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
