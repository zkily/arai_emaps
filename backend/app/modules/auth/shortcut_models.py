"""サイドバー常用ページ ORM"""
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class UserPinnedPage(Base):
    __tablename__ = "user_pinned_pages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    path = Column(String(255), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class UserPageVisit(Base):
    __tablename__ = "user_page_visits"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    path = Column(String(255), nullable=False)
    visit_count = Column(Integer, nullable=False, default=1)
    last_visited_at = Column(DateTime, nullable=False)
