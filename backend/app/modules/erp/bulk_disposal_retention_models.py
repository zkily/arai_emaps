"""大量廃棄・保留品記録 (bulk_disposal_retention_records) モデル"""
from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class BulkDisposalRetentionRecord(Base):
    __tablename__ = "bulk_disposal_retention_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    occurred_date = Column(Date, nullable=False, comment="発生日")
    report_category = Column(String(20), nullable=False, comment="報告区分")
    process_name = Column(String(20), nullable=False, comment="発生工程")
    product_cd = Column(String(50), nullable=True, comment="製品CD")
    product_name = Column(String(200), nullable=False, comment="製品名")
    quantity = Column(Integer, nullable=False, default=0, comment="発生本数")
    handling_status = Column(String(10), nullable=False, default="未処理", comment="処理")
    processed_date = Column(Date, nullable=True, comment="処理日付")
    processing_deadline_date = Column(Date, nullable=True, comment="期間内処理期限（保留品）")
    management_no = Column(String(50), nullable=True, comment="管理No")
    remarks = Column(Text, nullable=True, comment="備考")
    created_by_user_id = Column(Integer, nullable=True, comment="登録者ID")
    updated_by_user_id = Column(Integer, nullable=True, comment="更新者ID")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="作成日時")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新日時"
    )
