"""
認証APIエンドポイント
ログイン、ログアウト、ユーザー情報取得
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta
from app.core.datetime_utils import now_jst
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash, decode_access_token
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# スキーマ定義
class UserBase(BaseModel):
    username: str
    email: str
    role: str = "user"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    full_name: Optional[str] = None
    is_active: bool = True
    permissions: list[str] = []
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """ユーザー名またはメールアドレスでユーザーを取得"""
    # ユーザー名で検索
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    
    # ユーザー名で見つからない場合、メールアドレスで検索
    if not user:
        result = await db.execute(
            select(User).where(User.email == username)
        )
        user = result.scalar_one_or_none()
    
    return user


async def verify_token_and_get_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """トークンを検証してユーザーを取得（単一デバイスログイン対応）
    
    この関数は、すべての認証が必要なAPIエンドポイントで使用する必要があります。
    これにより、他のデバイスでログインした場合、このトークンが無効になります。
    
    ロジック：
    1. リクエストのトークン（Token_A）を取得
    2. データベースからユーザーの last_login_token（Token_B）を取得
    3. Token_A == Token_B なら放行、Token_A != Token_B なら拒否
    """
    # トークンをデコードしてユーザー名を取得
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが無効です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが無効です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # データベースからユーザーを取得
    user = await get_user_by_username(db, username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )
    
    # アカウントが無効な場合
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このアカウントは無効化されています",
        )
    
    # 単一デバイスログイン: トークンを直接比較
    # リクエストのトークン（Token_A）とデータベースの last_login_token（Token_B）を比較
    request_token = token  # Token_A
    stored_token = user.last_login_token  # Token_B
    
    # デバッグ情報 - 使用 logger.warning 确保输出
    verify_msg = f"[SINGLE_DEVICE_VERIFY] User: {user.username}, Request: {request_token[:40] if request_token else 'None'}..., Stored: {stored_token[:40] if stored_token else 'None'}..., Match: {stored_token == request_token if stored_token else 'No stored token'}"
    logger.warning(verify_msg)  # 使用 WARNING 级别确保输出
    print(verify_msg, flush=True)
    import sys
    sys.stderr.write(verify_msg + "\n")
    sys.stderr.flush()
    
    # last_login_tokenがNULLの場合は、まだログインしていない（初回ログイン）とみなす
    # ただし、既にログインしている場合は、トークンが一致する必要がある
    if stored_token is not None and stored_token != request_token:
        mismatch_msg = f"[SINGLE_DEVICE_MISMATCH] ❌ TOKEN MISMATCH! User {user.username} logged in on another device. Stored: {stored_token[:40]}..., Request: {request_token[:40]}..."
        logger.error(mismatch_msg)  # 使用 ERROR 级别确保输出
        print(mismatch_msg, flush=True)
        import sys
        sys.stderr.write(mismatch_msg + "\n")
        sys.stderr.flush()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="このアカウントは他のデバイスでログインされています。再度ログインしてください。",
            headers={"WWW-Authenticate": "Bearer", "X-Force-Logout": "true"},
        )
    
    success_msg = f"[SINGLE_DEVICE_VERIFY] ✅ Token verified successfully for user {user.username}"
    logger.info(success_msg)
    print(success_msg, flush=True)
    
    return user


def get_user_permissions(role: str) -> list[str]:
    """ロールに基づいて権限を取得（admin: 全権限 / manager, worker, user: 読み書き / guest, viewer: 閲覧のみ）"""
    if role == "admin":
        return ["all"]
    if role in ("guest", "viewer"):
        return ["read"]
    return ["read", "write"]


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """ログインエンドポイント - データベースからユーザーを検証"""
    # データベースからユーザーを取得
    user = await get_user_by_username(db, login_data.username)
    
    # ユーザーが存在しない場合
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # アカウントが無効な場合
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このアカウントは無効化されています",
        )
    
    # パスワードを検証
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # アクセストークンを生成
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # トークンを直接データベースに保存（単一デバイスログイン用）
    # これにより、他のデバイスでログインすると、このトークンが無効になる
    old_token = user.last_login_token
    user.last_login_token = access_token
    user.last_login_at = now_jst()
    await db.commit()
    await db.refresh(user)
    
    # デバッグ: トークンが正しく保存されたか確認
    # 使用 logger 和 print 双重输出确保能看到
    log_msg = f"[SINGLE_DEVICE_LOGIN] User {user.username} logged in. Token: {access_token[:50]}... Updated last_login_token"
    logger.info(log_msg)
    logger.warning(log_msg)  # 使用 WARNING 级别确保输出
    print(log_msg, flush=True)
    import sys
    sys.stderr.write(log_msg + "\n")
    sys.stderr.flush()
    
    # WebSocket経由で他のデバイスに通知（既にログインしていた場合）
    if old_token and old_token != access_token:
        try:
            from app.api.websocket import notify_user_logged_in_elsewhere
            await notify_user_logged_in_elsewhere(user.username, access_token)
            logger.info(f"[WebSocket] Notified other devices for user {user.username}")
        except Exception as e:
            logger.error(f"[WebSocket] Failed to notify other devices: {e}")
    
    # ユーザー権限を取得
    permissions = get_user_permissions(user.role)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "permissions": permissions,
        }
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(verify_token_and_get_user),
    db: AsyncSession = Depends(get_db)
):
    """ログアウトエンドポイント"""
    # トークンをクリア（ログアウト）
    current_user.last_login_token = None
    await db.commit()
    
    logger.info(f"[SINGLE_DEVICE] User {current_user.username} logged out")
    print(f"[SINGLE_DEVICE] User {current_user.username} logged out")
    
    return {"message": "ログアウトしました"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(verify_token_and_get_user)
):
    """現在のユーザー情報取得"""
    # ユーザー権限を取得
    permissions = get_user_permissions(current_user.role)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "permissions": permissions,
    }

