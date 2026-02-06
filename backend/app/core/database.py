"""
データベース接続設定
SQLAlchemyを使用した非同期データベース接続
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# データベースエンジンの作成
# echo: 開発時のみ True に（SQL ログで起動が重くなるため、通常は False）
engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# セッションファクトリーの作成
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ベースクラスの作成
Base = declarative_base()


async def get_db():
    """データベースセッションの依存性注入"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

