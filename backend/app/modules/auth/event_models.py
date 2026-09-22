"""個人イベント ORM"""
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, String, Text, func

from app.core.database import Base


class UserEvent(Base):
    __tablename__ = "user_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=True)
    location = Column(String(255), nullable=True)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    all_day = Column(Integer, nullable=False, default=0)
    color = Column(String(20), nullable=True)
    visibility = Column(String(20), nullable=False, default="department")
    recurrence_rule = Column(String(20), nullable=True)
    recurrence_until = Column(Date, nullable=True)
    recurrence_exdates = Column(Text, nullable=True)
    remind_offset_minutes = Column(Integer, nullable=True)
    remind_at = Column(DateTime, nullable=True)
    reminded_at = Column(DateTime, nullable=True)
    last_reminded_occurrence = Column(Date, nullable=True)
    reminded_dates = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
