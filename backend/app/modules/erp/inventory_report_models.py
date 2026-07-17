"""在庫報告書（四半期・半期・年間）モデル"""
from sqlalchemy import BigInteger, Column, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class InventoryQuarterlyReport(Base):
    __tablename__ = "inventory_quarterly_reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    fiscal_year = Column(Integer, nullable=False, comment="年度（4月始まり）")
    quarter = Column(
        SmallInteger,
        nullable=False,
        comment="報告期間コード 1-4=Q1-Q4, 5=上期, 6=下期, 7=年間",
    )
    title = Column(String(200), nullable=False, comment="報告書タイトル")
    status = Column(String(20), nullable=False, default="draft", comment="draft/final")
    payload_json = Column(Text, nullable=False, comment="集計スナップショットJSON")
    scrap_overrides_json = Column(Text, nullable=True, comment="廃棄率手動上書きJSON")
    executive_summary = Column(Text, nullable=True, comment="報告向け要約")
    action_items = Column(Text, nullable=True, comment="改善アクション")
    notes = Column(Text, nullable=True, comment="備考")
    generated_at = Column(DateTime, nullable=True, comment="集計実行日時")
    created_by_user_id = Column(Integer, nullable=True, comment="作成者ID")
    updated_by_user_id = Column(Integer, nullable=True, comment="更新者ID")
    created_at = Column(DateTime, default=func.now(), nullable=True, comment="作成日時")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True, comment="更新日時"
    )
