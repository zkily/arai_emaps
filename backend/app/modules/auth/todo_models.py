"""ユーザー個人 TODO ORM"""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class UserTodo(Base):
    __tablename__ = "user_todos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(String(500), nullable=False)
    is_done = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
