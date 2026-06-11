"""
認証APIエンドポイント
ログイン、ログアウト、ユーザー情報取得
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
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
from app.modules.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


def _client_ip(request: Request) -> str:
    """X-Forwarded-For / X-Real-IP または request.client からクライアントIPを取得"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host or ""
    return ""


def _user_agent(request: Request) -> str:
    return (request.headers.get("user-agent") or "")[:500]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# スキーマ定義
class UserBase(BaseModel):
    username: str
    email: str
    role: str = "user"


class UserCreate(UserBase):
    password: str


class OperationPermissionPayload(BaseModel):
    module: str
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False
    can_export: bool = False
    can_approve: bool = False


class UserResponse(UserBase):
    id: int
    full_name: Optional[str] = None
    is_active: bool = True
    permissions: list[str] = []
    menu_codes: list[str] = []
    operation_permissions: list[OperationPermissionPayload] = []
    department_id: Optional[int] = None
    department_name: Optional[str] = None

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
    
    # アカウントが無効な場合（401 にすることでフロントでログアウト・ログインへリダイレクトさせる）
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="このアカウントは無効化されています。管理者にお問い合わせください。",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 単一デバイスログイン: トークンを直接比較
    # リクエストのトークン（Token_A）とデータベースの last_login_token（Token_B）を比較
    request_token = token  # Token_A
    stored_token = user.last_login_token  # Token_B
    
    # last_login_tokenがNULLの場合は、まだログインしていない（初回ログイン）とみなす
    # ただし、既にログインしている場合は、トークンが一致する必要がある
    if stored_token is not None and stored_token != request_token:
        logger.warning(
            "[SINGLE_DEVICE_MISMATCH] user=%s logged in on another device", user.username
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="このアカウントは他のデバイスでログインされています。再度ログインしてください。",
            headers={"WWW-Authenticate": "Bearer", "X-Force-Logout": "true"},
        )
    
    return user


async def get_db_and_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> tuple[AsyncSession, User]:
    """logout 用: 同一セッションの (db, user) を返し、db.commit() で last_login_token を永続化できるようにする"""
    user = await verify_token_and_get_user(token=token, db=db)
    return (db, user)


async def _resolve_department_name(db: AsyncSession, department_id: Optional[int]) -> Optional[str]:
    """organizations から所属部門の表示名を取得"""
    if department_id is None:
        return None
    from app.modules.system.models import Organization

    result = await db.execute(select(Organization).where(Organization.id == department_id))
    org = result.scalar_one_or_none()
    return org.name if org else None


def get_user_permissions(role: str) -> list[str]:
    """ロールに基づいて権限を取得（admin: 全権限 / manager, worker, user: 読み書き / guest, viewer: 閲覧のみ）"""
    if role == "admin":
        return ["all"]
    if role in ("guest", "viewer"):
        return ["read"]
    return ["read", "write"]


async def get_user_menu_codes(db: AsyncSession, user: User) -> list[str]:
    """ユーザーがアクセス可能なメニューコード一覧（user_roles → role_menu_permissions から集約）"""
    from app.modules.system.models import Menu, RoleMenuPermission, UserRole

    role = user.role if user.role else "user"

    if role == "admin":
        result = await db.execute(
            select(Menu.code)
            .where(Menu.is_active == True)
            .order_by(Menu.sort_order, Menu.id)
        )
        return list(result.scalars().all())

    result = await db.execute(
        select(Menu.code)
        .distinct()
        .join(RoleMenuPermission, RoleMenuPermission.menu_id == Menu.id)
        .join(UserRole, UserRole.role_id == RoleMenuPermission.role_id)
        .where(UserRole.user_id == user.id, Menu.is_active == True)
        .order_by(Menu.code)
    )
    return list(result.scalars().all())


def _empty_operation_permission(module: str) -> dict:
    return {
        "module": module,
        "can_create": False,
        "can_edit": False,
        "can_delete": False,
        "can_export": False,
        "can_approve": False,
    }


def _full_operation_permission(module: str) -> dict:
    return {
        "module": module,
        "can_create": True,
        "can_edit": True,
        "can_delete": True,
        "can_export": True,
        "can_approve": True,
    }


def _fallback_operation_permissions(role: str) -> list[dict]:
    """role_operation_permissions 未設定時: users.role の read/write にフォールバック"""
    from app.core.operation_modules import OPERATION_MODULES

    perms = get_user_permissions(role)
    can_write = "all" in perms or "write" in perms
    can_read = can_write or "read" in perms
    return [
        {
            "module": module,
            "can_create": can_write,
            "can_edit": can_write,
            "can_delete": can_write,
            "can_export": can_read,
            "can_approve": can_write,
        }
        for module in OPERATION_MODULES
    ]


async def get_user_operation_permissions(db: AsyncSession, user: User) -> list[dict]:
    """user_roles → role_operation_permissions をモジュール単位で OR 集約"""
    from app.modules.system.models import RoleOperationPermission, UserRole
    from app.core.operation_modules import OPERATION_MODULES

    role = user.role if user.role else "user"
    if role == "admin":
        return [_full_operation_permission(module) for module in OPERATION_MODULES]

    result = await db.execute(
        select(RoleOperationPermission)
        .join(UserRole, UserRole.role_id == RoleOperationPermission.role_id)
        .where(UserRole.user_id == user.id)
    )
    rows = list(result.scalars().all())
    if not rows:
        return _fallback_operation_permissions(role)

    merged: dict[str, dict] = {}
    for row in rows:
        module = row.module
        if module not in merged:
            merged[module] = _empty_operation_permission(module)
        entry = merged[module]
        entry["can_create"] = entry["can_create"] or bool(row.can_create)
        entry["can_edit"] = entry["can_edit"] or bool(row.can_edit)
        entry["can_delete"] = entry["can_delete"] or bool(row.can_delete)
        entry["can_export"] = entry["can_export"] or bool(row.can_export)
        entry["can_approve"] = entry["can_approve"] or bool(row.can_approve)

    return [
        merged.get(module, _empty_operation_permission(module))
        for module in OPERATION_MODULES
    ]


async def build_user_auth_payload(db: AsyncSession, user: User) -> dict:
    """ログイン /me 共通のユーザー情報ペイロード"""
    role = user.role if user.role is not None else "user"
    dept_id = getattr(user, "department_id", None)
    return {
        "id": user.id,
        "username": user.username or "",
        "email": user.email or "",
        "full_name": user.full_name,
        "role": role,
        "is_active": bool(user.is_active) if user.is_active is not None else True,
        "permissions": get_user_permissions(role),
        "menu_codes": await get_user_menu_codes(db, user),
        "operation_permissions": await get_user_operation_permissions(db, user),
        "department_id": dept_id,
        "department_name": await _resolve_department_name(db, dept_id),
    }


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
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
    
    logger.info("[SINGLE_DEVICE_LOGIN] user=%s logged in", user.username)

    # WebSocket経由で他のデバイスに通知（既にログインしていた場合）
    if old_token and old_token != access_token:
        try:
            from app.modules.websocket.api import notify_user_logged_in_elsewhere
            await notify_user_logged_in_elsewhere(user.username, access_token)
            logger.info("[WebSocket] Notified other devices for user %s", user.username)
        except Exception as e:
            logger.error("[WebSocket] Failed to notify other devices: %s", e)
    
    # 操作ログに記録（遅延 import で循環参照を回避、テーブル未作成時は無視）
    try:
        from app.modules.system.settings_models import OperationLog
        op_log = OperationLog(
            user_id=user.id,
            username=user.username,
            action="login",
            module="auth",
            ip_address=_client_ip(request) or None,
            user_agent=_user_agent(request) or None,
        )
        db.add(op_log)
        await db.commit()
    except Exception as e:
        logger.warning("操作ログ記録に失敗しました（ログインは成功）: %s", e)
        await db.rollback()
    
    user_payload = await build_user_auth_payload(db, user)
    role = user.role if user.role else "user"
    if role != "admin" and not user_payload.get("menu_codes"):
        logger.warning(
            "[MENU_ACCESS] user=%s has no menu_codes — assign user_roles and role menu permissions",
            user.username,
        )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_payload,
    }


@router.post("/logout")
async def logout(
    request: Request,
    db_and_user: tuple[AsyncSession, User] = Depends(get_db_and_current_user),
):
    """ログアウトエンドポイント（同一セッションで last_login_token をクリアして永続化）"""
    db, current_user = db_and_user
    # トークンをクリア（ログアウト）
    current_user.last_login_token = None
    await db.commit()

    # 操作ログに記録（遅延 import で循環参照を回避、テーブル未作成時は無視）
    try:
        from app.modules.system.settings_models import OperationLog
        op_log = OperationLog(
            user_id=current_user.id,
            username=current_user.username,
            action="logout",
            module="auth",
            ip_address=_client_ip(request) or None,
            user_agent=_user_agent(request) or None,
        )
        db.add(op_log)
        await db.commit()
    except Exception as e:
        logger.warning("操作ログ記録に失敗しました（ログアウトは成功）: %s", e)
        await db.rollback()

    logger.info("[SINGLE_DEVICE] user=%s logged out", current_user.username)
    return {"message": "ログアウトしました"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db_and_user: tuple[AsyncSession, User] = Depends(get_db_and_current_user),
):
    """現在のユーザー情報取得"""
    try:
        db, current_user = db_and_user
        return await build_user_auth_payload(db, current_user)
    except Exception as e:
        logger.exception("GET /me でエラー: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー情報の取得に失敗しました",
        ) from e

