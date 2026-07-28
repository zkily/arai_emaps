"""生産検討会資料（月次 PPT）モデル"""
from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class ProductionReviewMeeting(Base):
    """月次生産検討会資料（編集可能な集計スナップショット）"""

    __tablename__ = "production_review_meetings"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    target_month = Column(String(7), nullable=False, unique=True, comment="対象月 YYYY-MM")
    status = Column(String(20), nullable=False, default="draft", comment="draft/final")
    data_json = Column(Text, nullable=False, comment="ページデータJSON")
    generated_at = Column(DateTime, nullable=True, comment="最終集計日時")
    created_by_user_id = Column(Integer, nullable=True, comment="作成者ID")
    updated_by_user_id = Column(Integer, nullable=True, comment="更新者ID")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="作成日時")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新日時"
    )


class ProductionReviewCapacity(Base):
    """生産検討会用 工程能力パラメータ（負荷率計算）"""

    __tablename__ = "production_review_capacity"
    __table_args__ = (UniqueConstraint("process_cd", name="uk_prc_process_cd"),)

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    process_cd = Column(String(50), nullable=False, comment="工程コード")
    process_name = Column(String(50), nullable=False, comment="工程名")
    equipment_label = Column(String(100), nullable=True, comment="設備・人員表示")
    standard_rate = Column(Integer, nullable=False, default=0, comment="標準能率 本/H")
    shift_label = Column(String(20), nullable=True, comment="標準稼働直")
    working_days = Column(Integer, nullable=False, default=0, comment="稼働日数（0=対象月カレンダー）")
    daily_regular_hours = Column(Integer, nullable=False, default=0, comment="日当たり定時H")
    sort_order = Column(Integer, nullable=False, default=0, comment="表示順")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="作成日時")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新日時"
    )
