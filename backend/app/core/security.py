"""
セキュリティ関連のユーティリティ
パスワードハッシュ化、JWT生成など
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib

from app.core.config import settings
from app.core.datetime_utils import JST

# パスワードハッシュ化コンテキスト
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードの検証
    
    bcryptは最大72バイトまでしか処理できないため、
    それより長いパスワードは自動的に切り詰めます。
    """
    # bcryptは最大72バイトまでしか処理できない
    # UTF-8エンコードして72バイトに制限
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """パスワードのハッシュ化
    
    bcryptは最大72バイトまでしか処理できないため、
    それより長いパスワードは自動的に切り詰めます。
    """
    # bcryptは最大72バイトまでしか処理できない
    # UTF-8エンコードして72バイトに制限
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWTアクセストークンの生成"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(JST) + expires_delta
    else:
        expire = datetime.now(JST) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.get_jwt_secret_key(),
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """JWTアクセストークンのデコード"""
    try:
        payload = jwt.decode(
            token,
            settings.get_jwt_secret_key(),
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """トークンのハッシュ値を生成（単一デバイスログイン用）"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

