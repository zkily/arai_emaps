"""
ユーザーモデル
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """ユーザーテーブルモデル"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="ユーザーID（主キー）")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="ユーザー名（ログインID、一意制約）")
    email = Column(String(100), unique=True, nullable=False, index=True, comment="メールアドレス（一意制約）")
    hashed_password = Column(String(255), nullable=False, comment="ハッシュ化されたパスワード")
    full_name = Column(String(100), nullable=True, comment="氏名（フルネーム）")
    role = Column(String(20), default="user", nullable=False, comment="ユーザーロール（admin:管理者、user:一般ユーザー、manager:マネージャー、worker:作業者、guest:ゲスト、viewer:閲覧者）")
    is_active = Column(Boolean, default=True, nullable=False, comment="アカウント有効フラグ（TRUE:有効、FALSE:無効）")
    last_login_token = Column(String(500), nullable=True, comment="最後にログインしたデバイスのトークン（単一デバイスログイン用）")
    department_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, comment="所属部門ID")
    two_factor_enabled = Column(Boolean, default=False, nullable=False, comment="二要素認証有効フラグ")
    last_login_at = Column(DateTime, nullable=True, comment="最終ログイン日時")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', role='{self.role}')>"

