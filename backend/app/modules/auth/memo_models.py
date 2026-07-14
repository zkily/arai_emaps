"""個人メモ ORM"""
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, String, Time, func

from app.core.database import Base


class UserMemo(Base):
    __tablename__ = "user_memos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(String(2000), nullable=True)
    memo_date = Column(Date, nullable=False)
    memo_time = Column(Time, nullable=True)
    remind_at = Column(DateTime, nullable=True)
    remind_offset_minutes = Column(Integer, nullable=True)
    color = Column(String(20), nullable=True)
    status = Column(Integer, nullable=False, default=0)
    reminded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
